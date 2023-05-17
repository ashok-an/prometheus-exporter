IMAGE_TAG = "ashoka007/crypto-exporter:1.0"

build:
	docker build --platform linux/amd64 -t $(IMAGE_TAG) . && docker push $(IMAGE_TAG)
