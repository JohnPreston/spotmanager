#!/usr/bin/env python
"""
script to manage spot instances provisionning
"""

from sys import exit
import boto3
from getAutoScalingGroup import *
from spotWorth import go_for_spot


def get_spot_tags(asg):
    """
    Function to get SpotPrice and SpotType from the ASG tags
    :param asg: autoscaling group object
    :return: dict() with the appropriate values
    """
    values = {}
    for tag in asg['Tags']:
        if tag['Key'] == 'SpotPrice':
            values['spot_bid'] = tag['Value']
        elif tag['Key'] == 'SpotType':
            values['spot_type'] = tag['Value']
    return values


def get_groups_names(stack_name):
    """
    Function to find the physical ID of resources logical IDs from CloudFormation Stack
    :param stack_name: Name of the CloudFormation stack
    :return: dict() containing the EC2 ASG names
    """

    print("Core stack : %s" % stack_name)

    stack_gpu = get_son_stack_name(stack_name, 'stackGPU')
    gpu_core_name = get_auto_scaling_group_name(stack_gpu, 'asgGPU')
    gpu_spot_name = get_auto_scaling_group_name(stack_gpu, 'asgGPUSpot')

    groups = {
        'spot': [gpu_spot_name],
        'core': [gpu_core_name]
    }

    return groups


def group_select(asg_name, vpc_id):
    """
    Function to pick up the right ASG for the job depending on SpotMarket price
    :param asg_name: Name of the EC2 ASG
    :param vpc_id: VPC ID where we would want to create the instances
    :return: code describing what happened
    """
    instances_count = get_asg_instances_count(asg_name)
    if instances_count == 0:
        group = get_asg(asg_name)
        spot_values = get_spot_tags(group)
        if go_for_spot(spot_values['spot_type'], vpc_id, float(spot_values['spot_bid'])):
            return 1
        else:
            return -1
    else:
        return -2


def spotmanager_handler(event, context=None):
    """
    Function to deploy MediaWorkers
    :param event: Lambda param data
    :param context: Lambda context data
    :return: String describing what the Lambda function did
    """

    vpc_id = None
    if 'vpc_id' in event.keys():
        vpc_id = event['vpc_id']
    else:
        vpc_id = get_vpc_id()
    if not isinstance(vpc_id, basestring) and vpc_id.startswith('vpc-'):
        print("Invalid VPC ID : %s" % vpc_id)
        exit(-1)

    groups_names = get_groups_names(event['stack_name'])
    for group in groups_names['spot']:
        selection = group_select(group, vpc_id)
        if selection == 1:
            policies = get_asg_policies(group)
            policy = get_asg_scale_up_policy(policies)
            if policy:
                trigger_policy(group, policy)
                return "Executed %s in %s for %s" % (policy, vpc_id, group)
        elif selection == -2:
            return "Already instances"
        elif selection == -1:
            return "Would go to the other ASG"


if __name__ == "__main__":
    event = {
        'vpc_id': 'vpc-id',
        'stack_name': 'stack-name'
    }
    print(spotmanager_handler(event, None))
