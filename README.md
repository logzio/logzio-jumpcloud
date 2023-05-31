# logzio-jumpcloud
Ship Jumpcloud logs to Logz.io. 

Collects Jumpcloud events every time interval, using the Jumpcloud API given in the configuration, and sends them to Logz.io.


## Getting Started
### Pull Docker Image

Download the `logzio/logzio-jumpcloud-shipper` image:
```
docker pull logzio/logzio-jumpcloud-shipper
```
### Mount a Host Directory as a Data Volume

Create a local directory and move into it:
```shell
mkdir logzio-jumpcloud-shipper
cd logzio-jumpcloud-shipper
```
### Configuration
Create and edit the configuration file and name it `config.yaml`. There are 2 sections of the configuration:

**logzio**
| Parameter Name | Description | Required/Optional | Default |
| --- | --- | --- | --- |
| url | The Logz.io Listener URL for your region with port 8071. https://listener.logz.io:8071 | Required | - |
| token | Your Logz.io log shipping token securely directs the data to your Logz.io account. | Required | - |

**Jumpcloud**
| Parameter Name | Description | Required/Optional | Default |
| --- | --- | --- | --- |
| jumpcloud_api | A dictionary containing the JumpCloud API configurations. | Required | - |
| start_date | The start date and time for querying the JumpCloud API in UTC time with the format of %Y-%m-%dT%H:%M:%S.%fZ. For example: 2023-05-04T12:30:00.000000Z. | Optional | The current date and time. |
| credentials | A dictionary containing the token for authenticating the JumpCloud API request. | Required | - |
| token | The JumpCloud API token. | Required | - |
| time_interval | The time interval for querying the JumpCloud API in minutes. | Optional |5m |

**`Config.yaml`**
```yaml
logzio:
 url: "https://listener.logz.io:8071"
 token: "<<LOGZIO_TOKEN>>"

jumpcloud_api:
   url: https://api.jumpcloud.com/insights/directory/v1/events
   start_date:
   credentials:
     token: "<<JUMPCLOUD_API_TOKEN>>"
   settings:
     time_interval:
```


### Run The Docker Container
```shell
docker run --name logzio-jumpcloud-shipper -v "$(pwd)":/app/src/shared logzio-jumpcloud-shipper
```
### Stop Docker Container
When you stop the container, the code will run until completion of the iteration. To make sure it will finish the iteration on time, please give it a grace period of 30 seconds when you run the docker stop command:
```shell
docker stop -t 30 logzio-jumpcloud-shipper
```

### Last Start Dates Text File
After every successful iteration of each API call, the last start date of the next iteration will be written to a file named `lastTime.txt`. Each line of the file starts with the API name and ends with the last start date in UTC time with the format of %Y-%m-%dT%H:%M:%S.%fZ.


You can find the `lastTime.txt` file inside the mounted host directory that you have created. If you have stopped the container, you can continue from the exact place you stopped by adding the last start date to the API filters in the configuration.


Note that the last start date should also be in UTC time with the format of %Y-%m-%dT%H:%M:%S.%fZ.




