#!/usr/bin/env python
"""
Script to get the right EC2 ASG name and details
"""

import boto3
from botocore.exceptions import ClientError

asg_client = boto3.client('autoscaling')
cf_client = boto3.client('cloudformation')


def get_asg_instances_count(asg_name):
    """
    Function to get all the instances of one ASG
    :param asg_name: name of the EC2 ASG
    :return: int
    """

    asg = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    if len(asg['AutoScalingGroups']) == 1:
        return len(asg['AutoScalingGroups'][0]['Instances'])
    else:
        print("Problem getting the asg. ASG # : %d" % len(asg))
        return -1

def get_asg(asg_name):
    """
    Function to get all the instances of one ASG
    :param asg_name: name of the EC2 ASG
    :return: int
    """

    asg = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    if len(asg['AutoScalingGroups']) == 1:
        return asg['AutoScalingGroups'][0]
    else:
        return None


def get_asg_policies(asg_name):
    """
    Function to get the ASG policies
    :return: policies
    """
    return asg_client.describe_policies(AutoScalingGroupName=asg_name)


def get_asg_scale_up_policy(policies):
    """
    """
    for policy in policies['ScalingPolicies']:
        stripped = policy['PolicyName'].strip().split('-')
        for strip in stripped:
            if strip.find("ScaleUp") != -1:
                return policy['PolicyName']


def get_son_stack_name(mother_name, resource_name):
    """
    Function to find the stackGPU name
    """
    try:
        son_stack_resource = cf_client.describe_stack_resource(StackName=mother_name, LogicalResourceId=resource_name)
        if son_stack_resource['StackResourceDetail']['ResourceType'] == "AWS::CloudFormation::Stack":
            son_stack_id = son_stack_resource['StackResourceDetail']['PhysicalResourceId']
            son_stack_name = son_stack_id.split('/')[1]
            return son_stack_name
        else:
            return None
    except:
        return None


def get_auto_scaling_group_name(stack_name, resource_name):
    """
    Function to find the EC2 ASG Name within nested stacks
    :param stack_name: name of the cloudformation "mother" stack
    :param resource_name: Name of the resource to designate the logical ID
    :return:
    """

    son_stack_resource = cf_client.describe_stack_resource(StackName=stack_name, LogicalResourceId=resource_name)
    if son_stack_resource['StackResourceDetail']['ResourceType'] == "AWS::AutoScaling::AutoScalingGroup":
        asg_id = son_stack_resource['StackResourceDetail']['PhysicalResourceId']
        return asg_id
    else:
        return None


def trigger_policy(asg_name, policy_name):
    """
    Function to trigger the scale-out policy
    """
    try:
        asg_client.execute_policy(AutoScalingGroupName=asg_name,PolicyName=policy_name,HonorCooldown=True)
    except ClientError as e:
        print(e['Code'])


if __name__ == '__main__':
    asg_name = get_auto_scaling_group_name('stackname', 'asgGPU', 'asgGPU')
    if type(asg_name)is not None:
        instances_count = get_asg_instances_count(asg_name)
        print(instances_count)
