from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elb,
    aws_logs,
    aws_servicediscovery as servicediscovery,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
    aws_s3 as s3
)
import aws_cdk as cdk

from constructs import Construct


class EphemeralStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.environment_name = "development"
        self.vpc = ec2.Vpc.from_lookup(self, id="VPC", is_default=True)

        self.cluster = ecs.Cluster(
            self,
            id=f"ephemeral-{self.environment_name}-cluster",
            cluster_name=f"ephemeral-{self.environment_name}-cluster",
            vpc=self.vpc,
        )
    #
    #     self.container_port = 8080
    #
        self.load_balancer_security_group = ec2.SecurityGroup(
            self,
            "alb_security_group",
            security_group_name="alb_sg",
            vpc=self.vpc,
        )

        self.cluster_security_group = ec2.SecurityGroup(
            self,
            "cluster_sg",
            security_group_name="cluster_sg",
            vpc=self.vpc
        )

        self.redis_security_group = ec2.SecurityGroup(self,
                                                      "redis_sg",
                                                      security_group_name="redis_sg",
                                                      vpc=self.vpc
                                                      )



        self.load_balancer_security_group.add_ingress_rule(
            peer=self.load_balancer_security_group,
            connection=ec2.Port.tcp(80),
            description="HTTP ingress"
        )

        self.cluster_security_group.add_ingress_rule(
            peer=self.load_balancer_security_group,
            connection=ec2.Port.tcp(8080),
            description="Cluster ALB ingress "
        )

        self.cluster_security_group.add_ingress_rule(
            peer = ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8899),
            description="Cluster ALB ingress "
        )

        self.redis_security_group.add_ingress_rule(
            peer=self.cluster_security_group,
            connection=ec2.Port.tcp(6379),
            description=""
        )


        ec2.CfnSecurityGroupIngress(
            self,
            "RedisInboundFromCluster",
            ip_protocol="TCP",
            source_security_group_id=self.cluster_security_group.security_group_id,
            to_port=6379,
            from_port=6379,
            group_id=self.redis_security_group.security_group_id
        )

        self.execution_task_role_policy = iam.ManagedPolicy.from_managed_policy_arn(self,
                                                                                    id=f"ephemeral-{self.environment_name}-execution-role-policy",
                                                                                    managed_policy_arn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy'
                                                                                    )
        secrets_manager_read_write_policy = iam.ManagedPolicy.from_managed_policy_arn(self,
                                                                                      id='ephemeral_api_secrets_read_write_policy',
                                                                                      managed_policy_arn='arn:aws:iam::aws:policy/AmazonSSMFullAccess'
                                                                                      )
        self.task_role = iam.Role(
            self,
            f"ephemeral-{self.environment_name}-role",
            role_name=f"ephemeral-{self.environment_name}-role",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
            managed_policies=[self.execution_task_role_policy]
        )

        self.execution_role = iam.Role(self, "FargateContainerRole",
                                       assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))

        self.ephemeral_api_port = 8080
        self.redis_port = 6379
        self.api_image_asset = ecr_assets.DockerImageAsset(self,
                                                           "ephemeral_api_image",
                                                           directory="..",
                                                           )
    #
        self.redis_image_asset = ecr_assets.DockerImageAsset(self,
                                                             "redis_image",
                                                             directory=".",
                                                             file="Dockerfile.redis"
                                                             )

        self.api_image = ecs.ContainerImage.from_docker_image_asset(self.api_image_asset)
        self.redis_image = ecs.ContainerImage.from_docker_image_asset(self.redis_image_asset)
        self.ephemeral_namespace = servicediscovery.PrivateDnsNamespace(
            self,
            id=f'ephemeral-{self.environment_name}-namespace',
            name=f'ephemeral-{self.environment_name}',
            vpc=self.vpc
        )

        # Create Fargate service for API
        self.load_balancer = self._create_appliation_load_balancer()

        self.api_service = self._create_api_fargate_service()
        self.redis = self._create_redis_fargate_service()

        self.target_group = elb.ApplicationTargetGroup(
            self,
            f"whiskeyjacktg",
            protocol=elb.ApplicationProtocol.HTTP,
            target_group_name=f"whiskeyjacktg",
            target_type=elb.TargetType.IP,
            targets=[self.api_service],
            vpc=self.vpc
        )

        self.listener = self.load_balancer.add_listener(
            "listener",
            port=80,
            default_target_groups=[self.target_group],
            protocol=elb.ApplicationProtocol.HTTP,
            open=True
        )
        #
        # self.listener = self.load_balancer.add_listener(
        #     "listener",
        #     port=443,fe
        #     default_target_groups=[self.target_group],
        #     protocol=elb.ApplicationProtocol.HTTPS,
        #     open=False
        # )
        #



    def _create_appliation_load_balancer(
            self,
    ) -> elb.ApplicationLoadBalancer:
        self.load_balancer = elb.ApplicationLoadBalancer(self,
                                                        id="ephemeral_api_loadbalancer",
                                                        security_group=self.load_balancer_security_group,
                                                        vpc=self.vpc,
                                                        internet_facing=True
                                                        )

        cdk.CfnOutput(
            self,
            "Load Balancer DNS",
            value=self.load_balancer.load_balancer_dns_name
        )
        return self.load_balancer

    def _create_api_fargate_service(self) -> ecs.FargateService:
        volume = ecs.Volume(name="WhiskeyJackVolume")
        mount_point = ecs.MountPoint(container_path="/usr/src/app/appdata", source_volume="WhiskeyJackVolume", read_only=False)
        api_log_group = aws_logs.LogGroup(
            self,
            'ephemeral_api_log_group',
            log_group_name='ephemeral_volumes_api_log_group',
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        api_task_definition = ecs.FargateTaskDefinition(
            self,
            id='api-task',
            family="api_task_def",
            cpu=512,
            memory_limit_mib=1024,
            task_role=self.task_role,
            execution_role=self.execution_role,
            volumes=[volume]
        )

        api_container = api_task_definition.add_container(
            "api-container",
            image=self.api_image,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=f"upload-logs",
                log_group=api_log_group
            ),
            environment={
                "PYTHONPATH": "/usr/src/app",
                "EPHEMERAL_DOCKER": "ecs",
            },
            port_mappings=[
                ecs.PortMapping(
                    container_port=8080,
                    host_port=8080
                )
            ]
        )

        upload_container = api_task_definition.add_container(
            "upload-container",
            image=self.api_image,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=f"ephemeral-{self.environment_name}-upload-logs",
                log_group=api_log_group
            ),
            command=["python", "rq_worker.py"],
            working_directory='/usr/src/app/whiskeyjack_upload/worker',
            environment={
                "PYTHONPATH": "/usr/src/app",
                "EPHEMERAL_DOCKER": "ecs",
            },
        )
        api_task_definition.add_container(
            "rq-monitor-container",
            image=ecs.ContainerImage.from_registry(name="pranavgupta1234/rqmonitor"),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="rq-monitor-logs",
                log_group=api_log_group
            ),
            environment={
                "RQ_MONITOR_REDIS_URL": "redis://redis.ephemeral-development:6379"
            },
            port_mappings=[
                ecs.PortMapping(container_port=8899, host_port=8899)
            ]
        )

        volume_from = ecs.VolumeFrom(
            read_only=False,
            source_container="api-container"
        )

        upload_container.add_mount_points(mount_point)
        upload_container.add_volumes_from(volume_from)


        ephemeral_service = ecs.FargateService(
            self,
            f'api-service',
            cluster=self.cluster,
            task_definition=api_task_definition,
            assign_public_ip=True,
            desired_count=1,
            security_groups=[self.cluster_security_group],
            cloud_map_options=ecs.CloudMapOptions(
                name='api',
                container_port=self.ephemeral_api_port,
                cloud_map_namespace=self.ephemeral_namespace,
                dns_record_type=servicediscovery.DnsRecordType.A
            ),
            service_name="ApiService"
        )
        return ephemeral_service

    def _create_redis_fargate_service(self) -> ecs.FargateService:
        self.redis_task_definition = ecs.FargateTaskDefinition(
            self,
            id="redis-task-def",
            family="redis_task_def",
            cpu=512,
            memory_limit_mib=1024,
            task_role=self.task_role,
            execution_role=self.execution_role
        )

        redis_log_group = aws_logs.LogGroup(
            self,
            'ephemeral_volumes_redis_log_group',
            log_group_name='ephemeral_volumes_redis_log_group',
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        redis_container = self.redis_task_definition.add_container(
            "ephemeral-redis-container",
            image=self.redis_image,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=f"ephemeral-{self.environment_name}-redis-logs",
                log_group=redis_log_group
            )
        )

        redis_port_mapping = ecs.PortMapping(container_port=self.redis_port, host_port=self.redis_port)
        redis_container.add_port_mappings(redis_port_mapping)

        redis_service = ecs.FargateService(
            self,
            f'redis-service',
            cluster=self.cluster,
            task_definition=self.redis_task_definition,
            assign_public_ip=True,
            desired_count=1,
            security_groups=[self.redis_security_group],
            cloud_map_options=ecs.CloudMapOptions(
                name='redis',
                container_port=self.ephemeral_api_port,
                cloud_map_namespace=self.ephemeral_namespace,
                dns_record_type=servicediscovery.DnsRecordType.A
            ),
            service_name="RedisService",

        )
        return redis_service
