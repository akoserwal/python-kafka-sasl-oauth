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
from confluent_kafka import Consumer
from confluent_kafka import DeserializingConsumer
import logging
import functools
import argparse
import time
from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import StringDeserializer
import requests


class User(object):
    """
    User record

    Args:
        name (str): User's name

        favorite_number (int): User's favorite number

        favorite_color (str): User's favorite color

    """
    def __init__(self, name=None, favorite_number=None, favorite_color=None):
        self.name = name
        self.favorite_number = favorite_number
        self.favorite_color = favorite_color


def dict_to_user(obj, ctx):
    """
    Converts object literal(dict) to a User instance.

    Args:
        ctx (SerializationContext): Metadata pertaining to the serialization
            operation.

        obj (dict): Object literal(dict)

    """
    if obj is None:
        return None

    return User(name=obj['name'],
                favorite_number=obj['favorite_number'],
                favorite_color=obj['favorite_color'])

def _get_token(args, config):
    """Note here value of config comes from sasl.oauthbearer.config below.
    It is not used in this example but you can put arbitrary values to
    configure how you can get the token (e.g. which token URL to use)
    """
    payload = {
        'grant_type': 'client_credentials',
        'scope': ' '.join(args.scopes)
    }
    resp = requests.post(args.token_url,
                         auth=(args.client_id, args.client_secret),
                         data=payload)
    token = resp.json()
    return token['access_token'], time.time() + float(token['expires_in'])


def consumer_config(args, json_deserializer):
    logger = logging.getLogger(__name__)
    string_deserializer = StringDeserializer('utf_8')
    return {
        'bootstrap.servers': args.bootstrap_servers,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'OAUTHBEARER',
        'key.deserializer': string_deserializer,
        'value.deserializer': json_deserializer,
        "group.id": args.group,
        'session.timeout.ms': 6000,
        'auto.offset.reset': 'earliest',
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

    json_deserializer = JSONDeserializer(schema_str,
                                         from_dict=dict_to_user)

    consumer_conf = consumer_config(args, json_deserializer)
    print(consumer_conf)
    consumer = DeserializingConsumer(consumer_conf)
    consumer.subscribe([topic])
    
    print('Consuming records to topic {}. ^C to exit.'.format(topic))
    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            user = msg.value()
            if user is not None:
                print("User record {}: name: {}\n"
                      "\tfavorite_number: {}\n"
                      "\tfavorite_color: {}\n"
                      .format(msg.key(), user.name,
                              user.favorite_number,
                              user.favorite_color))
        except KeyboardInterrupt:
            break

    consumer.close()


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
    parser.add_argument('-g', dest="group", default="example_serde_protobuf",
                        help="Consumer group")
    main(parser.parse_args())
