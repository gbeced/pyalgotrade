from python

RUN apt-get update -y && curl -sL https://deb.nodesource.com/setup_14.x | bash && apt-get install -y nodejs less jq

RUN npm install -g serverless
RUN serverless config tabcompletion install

# install Java for DynamoDB local instance
RUN apt-get install -y default-jre

# install AWS CLI

RUN cd /tmp && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install

## Python deps

# COPY requirements.txt requirements.txt

# RUN pip install -r requirements.txt