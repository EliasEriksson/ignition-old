FROM python:3.10-buster

# misc
RUN apt update
RUN apt install -y software-properties-common

# node.js install
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs

# go install
RUN wget https://golang.org/dl/go1.15.1.linux-amd64.tar.gz
RUN tar -C /usr/local -xzf go1.15.1.linux-amd64.tar.gz
RUN rm go1.15.1.linux-amd64.tar.gz
ENV PATH="${PATH}:/usr/local/go/bin"

# java install
RUN apt install -y default-jdk

# php install
#RUN apt-add-repository ppa:ondrej/pkg-gearman
#RUN apt update
RUN apt install -y php-cli

# C# install
RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN rm packages-microsoft-prod.deb
RUN apt update
RUN apt install -y apt-transport-https
RUN apt install -y dotnet-sdk-5.0

# C# setup to reduce time
RUN dotnet new console --output cs
RUN rm cs/Program.cs

RUN curl -fsSL https://deno.land/x/install/install.sh | sh
ENV PATH="${PATH}:/root/.deno/bin/"

# cleanup
RUN rm -rf /var/lib/apt/lists/*

# setup the client
WORKDIR /ignition
COPY requirements.txt /ignition/requirements.txt
RUN python -m pip install -r /ignition/requirements.txt

COPY ignition /ignition/ignition
COPY main.py /ignition/main.py

CMD ["python", "main.py", "client"]