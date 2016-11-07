"""
Script to create GPU instances with spot price
"""


from boto3 import client
from datetime import datetime as dt
from datetime import timedelta


ec2_client = client('ec2')


def find_subnets(vpc_id):
    """
    Function to find the subnet ID to place the Instance
    :param vpc_id: EC2 VPC ID
    :return: subnet object
    """

    filters = [
        {
            'Name': 'vpc-id',
            'Values': [
                vpc_id
            ]
        },
        {
            'Name': 'tag:Usage',
            'Values': [
                'ApplicationSubnet*'
            ]
        }
    ]
    subnet_id = ec2_client.describe_subnets(Filters=filters)
    return subnet_id


def get_spot_price(instance_type, az):
    """
    Function to get the latest spot price
    :param instance_type:
    :param az: Name of the EC2 AZ
    :return: string()
    """
    now = dt.utcnow()
    past_hour = now - timedelta(hours=1)
    price_history = ec2_client.describe_spot_price_history(StartTime=past_hour,
                                                           EndTime=now,
                                                           InstanceTypes=[instance_type],
                                                           ProductDescriptions=['Linux/UNIX (Amazon VPC)'],
                                                           AvailabilityZone=az
                                                           )

    total_price = 0
    for price_sample in price_history['SpotPriceHistory']:
        total_price += float(price_sample['SpotPrice'])
    avg = total_price / len(price_history['SpotPriceHistory'])
    return avg


def get_cheapest_az(instance_type, vpc_id):
    """
    :param instance_type: EC2 instance type
    :param vpc_id: ID of the VPC
    :return:
    """

    costs = []
    cheapest_cost = 0
    cheapest_az = None
    subnets = find_subnets(vpc_id)['Subnets']
    for subnet in subnets:
        price = get_spot_price(instance_type, subnet['AvailabilityZone'])
        costs.append({'az': subnet['AvailabilityZone'], 'price': price})

    if len(costs) > 1:
        cheapest_cost = costs[0]['price']
        for cost in costs:
            if cost['price'] <= cheapest_cost:
                cheapest_cost = cost['price']
                cheapest_az = cost['az']

    print "The cheapest for %s in %s is %f in %s" % (instance_type, vpc_id, cheapest_cost, cheapest_az)
    return {'az': cheapest_az, 'min_bid': cheapest_cost}


def go_for_spot(instance_type, vpc_id, max_bid):
    """
    Function to decide if run a Spot instance is doable according to max spot price.
    :param instance_type: EC2 instance type
    :param vpc_id: EC2 VPC ID where the EC2 instance will run
    :param max_bid: Current max bid on the ASG
    :return: boolean
    """

    cost = get_cheapest_az(instance_type, vpc_id)
    if cost['min_bid'] <= (max_bid - (0.15*max_bid)):
        print ("The current max bid (%f)is higher than market price (%f). Go for spot instance" %
               (max_bid, cost['min_bid']))
        return True
    else:
        print "The current max bid is lower than the market price. Go for on-demand"
        return False


if __name__ == '__main__':
    shall = go_for_spot('g2.2xlarge', 'vpc-bfe376db', 0.25)
    print shall
