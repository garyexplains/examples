# How to Run a ChatGPT-like AI Bot on a Raspberry Pi
Here is my step-by-step guide to running Large Language Models (LLMs) using llama.cpp on a Raspberry Pi. These instructions accompany my video [How to Run a ChatGPT-like AI on Your Raspberry Pi](https://youtu.be/idZctq7WIq4).

## Links

- [Introducing Code Llama, a state-of-the-art large language model for coding](https://ai.meta.com/blog/code-llama-large-language-model-coding/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Llama-2-7b-Chat-GGUF](https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF) - ([Q4_K_S](https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_S.gguf)) - ([Q2_K](https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF/resolve/main/llama-2-7b-chat.Q2_K.gguf))
- [Llama 2 13B Chat](https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF) - ([Q4_K_S](https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_S.gguf))
- [CodeLlama-7B-Instruct-GGUF](https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF) - ([Q4_K_S](https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_S.gguf))
- ~~[CodeLlama 7B Instruct - GGML](https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGML/tree/main) - ([Q4_K_S](https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGML/blob/main/codellama-7b-instruct.ggmlv3.Q4_K_S.bin))~~

## Prepare development environment
To start you need to have the C/C++ compiler, and tools like make and git.
```
sudo apt update
sudo apt install git g++ wget build-essential
```

## Download and compile llama.cpp
```
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make -j
```

## Download a LLM
You now need to download a language model. Pick one of the model below or download the model of your choice. Make sure you download the GGUF version (not the GGML variant).

These model files are several Gigabytes each, so make sure you have enough free space. If your SD Card is doesn't have the space you can try using some external storage, even a USB flash drive.

You can check the free space on the drive which holds your home directory using `df -h ~`
### Download a Llama 2 Chat 7B @ Q4_K_S
```
cd models
wget https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_S.gguf
```

### Download a Llama 2 Chat 7B @ Q2_K
```
cd models
wget https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF/resolve/main/llama-2-7b-chat.Q2_K.gguf
```

### Download a CodeLlama 7B
```
cd models
wget https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_S.gguf
```

## Test the LLM
Change directory back to the main llama.cpp directory, where the `main` binary has been built (i.e. `cd ..`)

```
./main -m models/<MODEL-NAME.gguf> -p "Building a website can be done in 10 simple steps:\nStep 1:" -n 400 -e
```

For example:
```
./main -m models/llama-2-7b-chat.Q4_K_S.gguf -p "Building a website can be done in 10 simple steps:\nStep 1:" -n 400 -e
```

Or:
```
./main -m models/codellama-7b-instruct.Q4_K_S.gguf -p "in python, write a function to create a Fibonacci sequence" -n 400 -e
```

## Interactive chat
Try this:
```
./main  -m models/llama-2-7b-chat.Q2_K.gguf --color \
       --ctx_size 2048 \
       -n -1 \
       -ins -b 256 \
       --top_k 10000 \
       --temp 0.2 \
       --repeat_penalty 1.1
```
Replace `llama-2-7b-chat.Q2_K.gguf` with your preferred model.

## Performance
The lower the quantization, the better the performance, but the lower the accuracy. An interesting test is whether a higher quantized 7B model is more accurate than a lower quantized 13B model. Let me know if you find out!

For a Raspberry Pi you should stick with Q4 or lower.


