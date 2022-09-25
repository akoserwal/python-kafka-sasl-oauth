# Using Confluent Kafka Python client with SASL/Oauth 

Get developer instance in few minutes

* Kafka: [Red Hat OpenShift Streams for Apache Kafka](https://developers.redhat.com/products/red-hat-openshift-streams-for-apache-kafka/getting-started)


* Service Registry: [Red Hat OpenShift Service Registry](https://console.redhat.com/application-services/service-registry)


# Setup
```bash
python3 -m pip install confluent-kafka
or
pip3 install confluent-kafka
```

Additional

```
pip3 install jsonschema
pip3 install schema_registry
pip3 install Faker
```


``` 
brew install librdkafka

or

https://github.com/edenhill/librdkafka
```
Set in .zshrc or bash_profile (For Mac OS)
```
export C_INCLUDE_PATH=/opt/homebrew/include
export LIBRARY_PATH=/opt/homebrew/lib
```

## Kafka & Service Registry

### Create a Kafka instance
### [Red Hat OpenShift Streams for Apache Kafka](https://developers.redhat.com/products/red-hat-openshift-streams-for-apache-kafka/getting-started)

### Create a Service Registry instance
### [Red Hat OpenShift Service Registry](https://console.redhat.com/application-services/service-registry)


## Create Service account & assign permission for Kafka & Service Registry

```export service_account_client_id=```

```export service_account_secret=```

# Configure the bootstrap url, topic, token_url, & registry schema url.

```export bootstrap_url= ```

```export token_url=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token```

```export topic=```

```export registryschema=```

# Run Producer

```
python producer_oauth.py -b $bootstrap_url --token-url $token_url --client $service_account_client_id --secret $service_account_secret --scopes api.iam.service_accounts -t $topic -s $registryschema
```
# Set the consumer group

`export consumer_group=`

# Run Consumer

```
python consumer_oauth.py -b $bootstrap_url --token-url $token_url --client $service_account_client_id --secret $service_account_secret --scopes api.iam.service_accounts -t $topic -g $consumer_group -s $registryschema
```

