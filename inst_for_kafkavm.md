# EC-Team-17-distributed-logging-system

Setup for the kafka VM
```
sudo systemctl start zookeeper
sudo systemctl start kafka
sudo systemctl enable zookeeper
sudo systemctl enable kafka
sudo systemctl daemon-reload
#verify if kafka and zookeeper have started
sudo systemctl status zookeeper
sudo systemctl status kafka

#create of topics
cd /opt/kafka
bin/kafka-topics.sh --create cache.registration --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
bin/kafka-topics.sh --create cache.log.info --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
bin/kafka-topics.sh --create cache.log.error --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
bin/kafka-topics.sh --create cache.log.warn --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
bin/kafka-topics.sh --create cache.heartbeat --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
bin/kafka-topics.sh --create cache.registry --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

#verify if topics are created
bin/kafka-topics.sh --list --bootstrap-server localhost:9092

#consumer
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic cache.log.info

```
