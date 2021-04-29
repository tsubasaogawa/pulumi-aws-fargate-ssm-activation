from pulumi import export, Output, ResourceOptions
import pulumi_aws as aws
import datetime
import json


project_name = 'fargate-ssm-activation'
platform_version = '1.4.0'
cidr_base = '10.1.0.0'
region = 'ap-northeast-1'
image = project_name
expire_timedelta = datetime.timedelta(days=7)
tz = datetime.timezone(datetime.timedelta(hours=+9), 'JST')

# Network

vpc = aws.ec2.Vpc(f'{project_name}-vpc',
	cidr_block=f'{cidr_base}/24',
	tags={
		'Name': f'{project_name}-vpc',
	}
)
subnet = aws.ec2.Subnet(f'{project_name}-subnet',
	vpc_id=vpc.id,
	cidr_block=f'{cidr_base}/28',
	tags={
		'Name': f'{project_name}-subnet',
	}
)

igw = aws.ec2.InternetGateway(f'{project_name}-igw',
    vpc_id=vpc.id,
	tags={
		'Name': f'{project_name}-igw',
	}
)

route_table = aws.ec2.RouteTable(f'{project_name}-rt',
	routes=[
		{
            'cidr_block': "0.0.0.0/0",
            'gateway_id': igw.id,
		},
	],
    vpc_id=vpc.id,
	tags={
		'Name': f'{project_name}-rt',
	}
)

route_table_association = aws.ec2.RouteTableAssociation(
    f'{project_name}-rt-association',
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

group = aws.ec2.SecurityGroup(f'{project_name}-sg',
	vpc_id=vpc.id,
	description='Block ingress',
  	egress=[aws.ec2.SecurityGroupEgressArgs(
		protocol='-1',
		from_port=0,
		to_port=0,
		cidr_blocks=['0.0.0.0/0'],
	)],
	tags={
		'Name': f'{project_name}-sg',
	}
)

# SSM Activation

activation_role = aws.iam.Role(f'{project_name}-activation-role',
	assume_role_policy=json.dumps({
		'Version': '2012-10-17',
		'Statement': {
			'Effect': 'Allow',
			'Principal': {
				'Service': 'ssm.amazonaws.com'
			},
			'Action': 'sts:AssumeRole',
		}
	}),
	tags={
		'Name': f'{project_name}-activation-role',
	}
)

activation_rpa = aws.iam.RolePolicyAttachment(f'{project_name}-activation-role-policy',
    role=activation_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
)

activation = aws.ssm.Activation(f'{project_name}-activation',
    description=f'Activation for {project_name}',
    iam_role=activation_role.id,
    registration_limit=100,
	expiration_date=(datetime.datetime.now(tz) + expire_timedelta).strftime('%Y-%m-%dT%H:%M:%SZ'),
    opts=ResourceOptions(
		depends_on=[activation_rpa]
	)
)

# ECR

repository = aws.ecr.Repository(f'{project_name}-repository',
	name=f'{project_name}-repository',
	image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
	tags={
		'Name': f'{project_name}-repository',
	}
)

# CloudWatch Logs

log_group = aws.cloudwatch.LogGroup(f'/{project_name}',
    tags={
        'Name': f'/{project_name}',
	}
)

# ECS

task_role = aws.iam.Role(f'{project_name}-task-role',
	assume_role_policy=json.dumps({
		'Version': '2008-10-17',
		'Statement': [{
			'Sid': '',
			'Effect': 'Allow',
			'Principal': {
				'Service': 'ecs-tasks.amazonaws.com'
			},
			'Action': 'sts:AssumeRole',
		}]
	}),
	tags={
		'Name': f'{project_name}-task-role',
	}
)

task_rpa = aws.iam.RolePolicyAttachment(f'{project_name}-task-role-policy',
	role=task_role.name,
	policy_arn='arn:aws:iam::aws:policy/CloudWatchLogsFullAccess',
)

task_execution_role = aws.iam.Role(f'{project_name}-task-execution-role',
	assume_role_policy=json.dumps({
		'Version': '2008-10-17',
		'Statement': [{
			'Sid': '',
			'Effect': 'Allow',
			'Principal': {
				'Service': 'ecs-tasks.amazonaws.com'
			},
			'Action': 'sts:AssumeRole',
		}]
	}),
	tags={
		'Name': f'{project_name}-task-execution-role',
	}
)

task_execution_rpa = aws.iam.RolePolicyAttachment(f'{project_name}-task-execution-role-policy',
	role=task_execution_role.name,
	policy_arn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
)

task_definition = aws.ecs.TaskDefinition(f'{project_name}-task-definition',
    family=project_name,
    cpu='256',
    memory='512',
    network_mode='awsvpc',
    requires_compatibilities=['FARGATE'],
	task_role_arn=task_role.arn,
    execution_role_arn=task_execution_role.arn,
    container_definitions=Output.all(
		repository.repository_url,
		activation.id,
		activation.activation_code,
		log_group.id
	).apply(lambda args: json.dumps([{
		'name': project_name,
		'image': args[0] + ':latest',
		'environment': [
			{
				'name': 'ACTIVATION_ID',
				'value': args[1],
			},
			{
				'name': 'ACTIVATION_CODE',
				'value': args[2],
			},
			{
				'name': 'REGION',
				'value': region,
			}
		],
		'logConfiguration': {
			'logDriver': 'awslogs',
			'options': {
				'awslogs-group': args[3],
				'awslogs-region': region,
				'awslogs-stream-prefix': 'fargate'
			}
		}
	}])),
)

cluster = aws.ecs.Cluster(f'{project_name}-cluster')

service = aws.ecs.Service(f'{project_name}-service',
	cluster=cluster.arn,
    desired_count=1,
    launch_type='FARGATE',
    task_definition=task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
		assign_public_ip=True,
		subnets=[subnet.id],
		security_groups=[group.id],
	),
	platform_version=platform_version,
)

# Output

export('ecr_repository', repository.repository_url)
