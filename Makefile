IMAGE_TAG = "ashoka007/crypto-exporter:1.0"
CONTAINER = "crypto-exporter"

build:
	docker build --platform linux/amd64 -t $(IMAGE_TAG) . && docker push $(IMAGE_TAG)

crypto:
	- docker rm -f $(CONTAINER)
	docker run -d --name=$(CONTAINER) -p 8000:8000 -e QUERY_INTERVAL_SECONDS=5 $(IMAGE_TAG)

run:
	docker-compose up -d 

