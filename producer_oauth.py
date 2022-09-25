#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 Confluent Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# This uses OAuth client credentials grant:
# https://www.oauth.com/oauth2-servers/access-tokens/client-credentials/
# where client_id and client_secret are passed as HTTP Authorization header
#

import logging
import functools
import argparse
import time
from uuid import uuid4
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
import requests
from faker import Faker

class User(object):
    """
    User record

    Args:
        name (str): User's name

        favorite_number (int): User's favorite number

        favorite_color (str): User's favorite color

        address(str): User's address; confidential

    """
    def __init__(self, name, address, favorite_number, favorite_color):
        self.name = name
        self.favorite_number = favorite_number
        self.favorite_color = favorite_color
        # address should not be serialized, see user_to_dict()
        self._address = address


def user_to_dict(user, ctx):
    """
    Returns a dict representation of a User instance for serialization.

    Args:
        user (User): User instance.

        ctx (SerializationContext): Metadata pertaining to the serialization
            operation.

    Returns:
        dict: Dict populated with user attributes to be serialized.

    """
    # User._address must not be serialized; omit from dict
    return dict(name=user.name,
                favorite_number=user.favorite_number,
                favorite_color=user.favorite_color)

def _get_token(args, config):
    payload = {
        'grant_type': 'client_credentials',
        'scope': ' '.join(args.scopes)
    }
    resp = requests.post(args.token_url,
                         auth=(args.client_id, args.client_secret),
                         data=payload)
    token = resp.json()
    print(token)
    return token['access_token'], time.time() + float(token['expires_in'])


def producer_config(args, json_serializer):
    logger = logging.getLogger(__name__)
    return {
        'bootstrap.servers': args.bootstrap_servers,
        'key.serializer': StringSerializer('utf_8'),
         'value.serializer': json_serializer,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'OAUTHBEARER',
        'oauth_cb': functools.partial(_get_token, args),
        'logger': logger.debug,
    }


def delivery_report(err, msg):
    """
    Reports the failure or success of a message delivery.

    Args:
        err (KafkaError): The error that occurred on None on success.

        msg (Message): The message that was produced or failed.

    Note:
        In the delivery report callback the Message.key() and Message.value()
        will be the binary format as encoded by any configured Serializers and
        not the same object that was passed to produce().
        If you wish to pass the original object(s) for key and value to delivery
        report callback we recommend a bound callback or lambda where you pass
        the objects along.

    """
    if err is not None:
        print('Delivery failed for User record {}: {}'.format(msg.key(), err))
        return
    print('User record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))


def main(args):
    topic = args.topic

    schema_str = """
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "User",
      "description": "Kafka Python User",
      "type": "object",
      "properties": {
        "name": {
          "description": "User's name",
          "type": "string"
        },
        "favorite_number": {
          "description": "User's favorite number",
          "type": "number",
          "exclusiveMinimum": 0
        },
        "favorite_color": {
          "description": "User's favorite color",
          "type": "string"
        }
      },
      "required": [ "name", "favorite_number", "favorite_color" ]
    }
    """
    s = args.client_id+':'+args.client_secret
    schema_registry_conf = {'url': args.schema_registry, 'basic.auth.user.info': s}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    json_serializer = JSONSerializer(schema_str, schema_registry_client, user_to_dict)

    producer_conf = producer_config(args,json_serializer)
    print(producer_conf)
    producer = SerializingProducer(producer_conf)
    fake = Faker()


    print('Producing records to topic {}. ^C to exit.'.format(topic))
    while True:
        # Serve on_delivery callbacks from previous calls to produce()
        producer.poll(0.0)
        try:
            user_name = fake.name()
            user_address = fake.address()
            user_favorite_number = int(1)
            user_favorite_color = "blue"
            user = User(name=user_name,
                        address=user_address,
                        favorite_color=user_favorite_color,
                        favorite_number=user_favorite_number)
            producer.produce(topic=topic, key=str(uuid4()), value=user,
                             on_delivery=delivery_report)
            time.sleep(5)
        except KeyboardInterrupt:
            break
        except ValueError:
            print("Invalid input, discarding record...")
            continue

    print('\nFlushing {} records...'.format(len(producer)))
    producer.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SerializingProducer OAUTH Example"
                                                 " with client credentials grant")
    parser.add_argument('-b', dest="bootstrap_servers", required=True,
                        help="Bootstrap broker(s) (host[:port])")
    parser.add_argument('-t', dest="topic", default="example_producer_oauth",
                        help="Topic name")
    parser.add_argument('-d', dest="delimiter", default="|",
                        help="Key-Value delimiter. Defaults to '|'"),
    parser.add_argument('--client', dest="client_id", required=True,
                        help="Client ID for client credentials flow")
    parser.add_argument('--secret', dest="client_secret", required=True,
                        help="Client secret for client credentials flow.")
    parser.add_argument('--token-url', dest="token_url", required=True,
                        help="Token URL.")
    parser.add_argument('--scopes', dest="scopes", required=True, nargs='+',
                        help="Scopes requested from OAuth server.")
    parser.add_argument('-s', dest="schema_registry", required=True,
                        help="Schema Registry (http(s)://host[:port]")

    main(parser.parse_args())
