# Using Confluent Kafka Python client with SASL/Oauth 

Get developer instance in few minutes

* Kafka: [Red Hat OpenShift Streams for Apache Kafka](https://developers.redhat.com/products/red-hat-openshift-streams-for-apache-kafka/getting-started)


* Service Registry: [Red Hat OpenShift Service Registry](https://console.redhat.com/application-services/service-registry)


# Setup

``` 
brew install librdkafka // for mac users

or

https://github.com/edenhill/librdkafka
```

```
 pip install --no-cache-dir -r requirements.txt
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

# Docker
```
docker build -f Dockerfile.producer -t producer_py --rm .
``` 
```
docker build -f Dockerfile.consumer -t consumer_py --rm .
```
```
docker run -it --name producer_py --rm producer_py --b $bootstrap_url --token-url $token_url --client $service_account_client_id --secret $service_account_secret --scopes api.iam.service_accounts -t $topic -s $registryschema
```
```
docker run -it --name consumer_py --rm consumer_py -b $bootstrap_url --token-url $token_url --client $service_account_client_id --secret $service_account_secret --scopes api.iam.service_accounts -t $topic -g $consumer_group -s $registryschema
```