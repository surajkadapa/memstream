.PHONY: build run clean

build:
	docker build --network=host -t cache-writer-service .

run:
	docker run -it --rm \
        --dns 8.8.8.8 \
        --dns 8.8.4.4 \
        --privileged \
        --ipc=host \
        --pid=host \
        cache-writer-service

clean:
	docker rmi cache-writer-service