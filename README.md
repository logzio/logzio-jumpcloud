# logzio-jumpcloud
Ship Jumpcloud logs to Logz.io. 

Collects Jumpcloud events every time interval, using the Jumpcloud API given in the configuration, and sends them to Logz.io.


## Getting Started
### Pull Docker Image

Download the `logzio/logzio-jumpcloud` image:
```
docker pull logzio/logzio-jumpcloud
```
### Mount a Host Directory as a Data Volume

Create a local directory and move into it:
```shell
mkdir logzio-jumpcloud
cd logzio-jumpcloud
```
### Configuration
Create and edit the configuration file and name it `config.yaml` in the `logzio-jumpcloud` folder that was created earlier. There are 2 sections of the configuration:

**logzio**

| Parameter Name | Description | Required/Optional                                                                  | Default |
| --- | --- |------------------------------------------------------------------------------------| --- |
| url | The Logz.io Listener URL for your region with port 8071. https://listener.logz.io:8071 | Required                                                                           | - |
| token | Your Logz.io log shipping token securely directs the data to your Logz.io account. | Required (also avilable via  [Environment variables](###use-environment-variable)) | - |

**Jumpcloud**

| Parameter Name | Description | Required/Optional                                                    | Default |
| --- | --- |----------------------------------------------------------------------| --- |
| jumpcloud_api | A dictionary containing the JumpCloud API configurations. | Required                                                             | - |
| start_date | The start date and time for querying the JumpCloud API in UTC time with the format of %Y-%m-%dT%H:%M:%S.%fZ. For example: 2023-05-04T12:30:00.000000Z. | Optional                                                             | The current date and time. |
| credentials | A dictionary containing the token for authenticating the JumpCloud API request. | Required (also avilable via  [Environment variables](###use-environment-variable)) | - |
| token | The JumpCloud API token. | Required                                                             | - |
| org_id | The organization ID for administered JumpCloud organizations. Needed for querying events if managing multiple organizations.	 | Optional                                                             | - |
| time_interval | The time interval for querying the JumpCloud API in minutes. | Optional                                                             |5m |

**`Config.yaml`**
```yaml

logzio:
 url: "https://listener.logz.io:8071"
 token: "<<LOGZIO_TOKEN>>"
jumpcloud_api:
   start_date:
   credentials:
     token: "<<JUMPCLOUD_API_TOKEN>>"
   settings:
     time_interval:
```


### Run The Docker Container
```shell
docker run --name logzio-jumpcloud -v "$(pwd)":/app/src/shared logzio/logzio-jumpcloud
```
### Use environment variable
To allow a more secure delivery of your API tokens you can use two environment variables exported instead of providing them in the configuration:
```shell
docker run --name logzio-jumpcloud -e LOGZIO_API_TOKEN=<<LOGZIO_TOKEN>> -e JUMPCLOUD_API_TOKEN=<<JUMPCLOUD_API_TOKEN>> -v "$(pwd)":/app/src/shared logzio/logzio-jumpcloud
```

### Stop Docker Container
When you stop the container, the code will run until completion of the iteration. To make sure it will finish the iteration on time, please give it a grace period of 30 seconds when you run the docker stop command:
```shell
docker stop -t 30 logzio/logzio-jumpcloud
```

### Last Start Dates Text File
After every successful iteration of each API call, the last start date of the next iteration will be written to a file named `lastTime.txt`. Each line of the file starts with the API name and ends with the last start date in UTC time with the format of %Y-%m-%dT%H:%M:%S.%fZ.


You can find the `lastTime.txt` file inside the mounted host directory that you have created. If you have stopped the container, you can continue from the exact place you stopped by adding the last start date to the API filters in the configuration.


Note that the last start date should also be in UTC time with the format of %Y-%m-%dT%H:%M:%S.%fZ.


### Changelog
- **0.0.3**:
  - Added support for `org_id` header in JumpCloud API requests to specify an administered organization.
  - Improved error handling for missing or invalid time_interval values.
- **0.0.2**:
  - Use event timestamp instead of ingested one @jmi926
  - Allow usage of `LOGZIO_API_TOKEN` and `JUMPCLOUD_API_TOKEN` ENV variables instead of file configuration @jmi926
  - Dockerfile - allow the user to be other than root @jmi926
- **0.0.1**: Initial release.


