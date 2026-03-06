FROM mongo:6.0.24

RUN mkdir -p /data/configdb /data/shard1

COPY init-cluster.sh /init-cluster.sh
RUN chmod +x /init-cluster.sh

EXPOSE 27017

#CMD ["/init-cluster.sh"]
