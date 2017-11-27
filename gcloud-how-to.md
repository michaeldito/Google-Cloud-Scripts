### copy remote directory to local host
`gcloud compute copy-files <instance-name>:~/REMOTE-DIR ~/LOCAL-DIR --zone <zone-name>`

### copy local file to google virtual machine
`gcloud compute scp ~/LOCAL-FILE-1 <instance-name>:~/REMOTE-DIR --zone <zone-name>`

### copy local file to google virtual machine as root user
`gcloud compute scp ~/LOCAL-FILE-1 root@<instance-name>:~/REMOTE-DIR --zone <zone-name>`

### ssh into a virtual machine
`gcloud compute ssh <instance-name> --zone <zone-name>`

### execute a command on the virtual machine
`gcloud compute ssh <instance-name> --zone <zone-name> --command <some-command>`
