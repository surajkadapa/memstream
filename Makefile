.PHONY: build run clean

build:
	docker build -t cache-writer-service .

run:
	docker run -it --rm \
		--privileged \
		--ipc=host \
		--pid=host \
		--network=host \
		cache-writer-service

clean:
	docker rmi cache-writer-service