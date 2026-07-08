import torch
from model import GPTConfig, GPT
from generate import generate

def load_data(filepath, block_size, batch_size, device, encoding="gpt2", retokenize=False):
    import os
    import json
    import numpy as np
    import tiktoken
    from tqdm import tqdm
    enc = tiktoken.get_encoding(encoding)

    if os.path.isdir(filepath):
        files = sorted(
            os.path.join(filepath, name) for name in os.listdir(filepath)
            if os.path.isfile(os.path.join(filepath, name))
        )
        if not files:
            raise FileNotFoundError(f"No files found in folder: {filepath}")
    else:
        files = [filepath]
    n_files = len(files)
    total_bytes = sum(os.path.getsize(f) for f in files)

    # Token cache as a sibling of the input (outside the folder, so the folder
    # loader never picks it up). Avoids re-tokenizing a multi-GB corpus each run.
    src = os.path.abspath(filepath)
    cache_bin = src + ".tokens.bin"
    cache_meta = cache_bin + ".meta.json"

    n_tokens = None
    if not retokenize and os.path.exists(cache_meta) and os.path.exists(cache_bin):
        meta = json.load(open(cache_meta))
        if (meta.get("encoding") == encoding
                and meta.get("n_files") == n_files
                and meta.get("total_bytes") == total_bytes):
            n_tokens = meta["n_tokens"]

    if n_tokens is None:
        # Stream-tokenize ONE file at a time straight to a raw int32 .bin file.
        # This is the fix for the memory blowup: we never hold the whole corpus
        # text or a giant Python list of token ints in RAM.
        print(f"Tokenizing {n_files} file{'s' if n_files != 1 else ''} -> {cache_bin}")
        n_tokens = 0
        # Stream each file in ~1MB reads, encoding only up to the last newline so
        # BPE merges and <|endoftext|> special tokens are never split across
        # calls. This keeps peak RAM ~constant even for a multi-GB single file.
        CHUNK = 1024 * 1024
        with open(cache_bin, "wb") as out:
            for f in tqdm(files, desc="Tokenizing", unit="file"):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        buf = ""
                        while True:
                            chunk = fh.read(CHUNK)
                            if not chunk:
                                break
                            buf += chunk
                            nl = buf.rfind("\n")
                            if nl == -1:
                                # no newline yet; flush only if buf is getting huge (rare)
                                if len(buf) > 4 * CHUNK:
                                    ids = enc.encode(buf, allowed_special="all")
                                    out.write(np.asarray(ids, dtype=np.int32).tobytes())
                                    n_tokens += len(ids)
                                    buf = ""
                                continue
                            safe, buf = buf[:nl + 1], buf[nl + 1:]
                            ids = enc.encode(safe, allowed_special="all")
                            out.write(np.asarray(ids, dtype=np.int32).tobytes())
                            n_tokens += len(ids)
                        if buf:
                            ids = enc.encode(buf, allowed_special="all")
                            out.write(np.asarray(ids, dtype=np.int32).tobytes())
                            n_tokens += len(ids)
                except (OSError, UnicodeDecodeError) as e:
                    tqdm.write(f"  skip {os.path.basename(f)}: {e}")
                    continue
        json.dump({"encoding": encoding, "n_files": n_files,
                   "total_bytes": total_bytes, "n_tokens": n_tokens,
                   "source": src}, open(cache_meta, "w"))

    # Memory-map the token file (copy-on-write): the OS pages slices in on
    # demand, so process RAM stays bounded even for a multi-GB corpus.
    arr = np.memmap(cache_bin, dtype=np.int32, mode="c", shape=(n_tokens,))
    tokens = torch.from_numpy(arr)
    n = int(0.9 * n_tokens)
    suffix = "s" if n_files != 1 else ""
    print(f"Dataset: {n_tokens:,} tokens ({n:,} train / {n_tokens - n:,} val), "
          f"{n_files} file{suffix}, vocab size: {enc.n_vocab}")

    def get_batch(split_tokens):
        ix = torch.randint(len(split_tokens) - block_size - 1, (batch_size,))
        x = torch.stack([split_tokens[i:i + block_size] for i in ix]).to(device).long()
        y = torch.stack([split_tokens[i + 1:i + block_size + 1] for i in ix]).to(device).long()
        return x, y

    get_train = lambda: get_batch(tokens[:n])
    get_val = lambda: get_batch(tokens[n:])
    return get_train, get_val, enc.n_vocab, enc, n
    
def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")     # Apple Silicon GPU
    elif torch.cuda.is_available():
        return torch.device("cuda")    # NVIDIA GPU
    return torch.device("cpu")
    
import math

def get_lr(step, warmup_steps, max_steps, max_lr, min_lr):
    if step < warmup_steps:
        return max_lr * (step + 1) / warmup_steps
    if step >= max_steps:
        return min_lr
    progress = (step - warmup_steps) / (max_steps - warmup_steps)
    return min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * progress))
    
import json
from tqdm import tqdm

def count_params(vocab_size, block_size, n_layer, n_embd):
    """Parameter count for the GPT in model.py (weight-tied embeddings counted once)."""
    embed = (vocab_size + block_size) * n_embd       # wte(=lm_head) + wpe
    per_block = 12 * n_embd * n_embd + 13 * n_embd   # attn(3+1)E^2 + mlp(4+4)E^2 + biases/LN
    blocks = n_layer * per_block
    final_ln = 2 * n_embd
    return embed + blocks + final_ln

def auto_config(vocab_size, block_size, n_train_tokens, tokens_per_param,
                head_dim=64, n_layer=None):
    """Pick a GPTConfig whose size gives ~n_train_tokens/tokens_per_param tokens per parameter.

    Searches (n_layer, n_embd) on a grid (n_embd multiples of head_dim, n_head = n_embd/head_dim)
    and returns the config whose parameter count is closest to n_train_tokens/tokens_per_param.
    Pass n_layer to pin depth and search width only.
    """
    target = n_train_tokens / tokens_per_param
    embd_choices = list(range(head_dim, 2048 + 1, head_dim))
    layer_choices = [n_layer] if n_layer else [2, 3, 4, 6, 8, 10, 12, 16, 20, 24]
    best = None
    for L in layer_choices:
        for E in embd_choices:
            n = count_params(vocab_size, block_size, L, E)
            err = abs(n - target)
            if best is None or err < best[0]:
                best = (err, L, E, n)
    _, L, E, n = best
    H = E // head_dim
    cfg = GPTConfig(vocab_size=vocab_size, block_size=block_size,
                    n_layer=L, n_head=H, n_embd=E)
    return cfg, n

def train(data_path, max_steps=5000, batch_size=64,
          n_layer=None, n_head=6, n_embd=None, block_size=256, encoding="gpt2",
          tokens_per_param=None, retokenize=False, resume=None):
    device = get_device()
    print(f"Using device: {device}")

    start_step = 0
    loss_log = {"steps": [], "train": [], "val": []}

    if resume:
        ckpt = torch.load(resume, map_location=device, weights_only=False)
        config = ckpt["config"]
        block_size = config.block_size          # must match the saved position embeddings
        start_step = ckpt["step"]
        loss_log = ckpt.get("loss_log", loss_log)
        print(f"Resuming from {resume} at step {start_step} "
              f"({config.n_layer}L/{config.n_head}H/{config.n_embd}D, "
              f"block_size {block_size}). Architecture flags are taken from the checkpoint.")
        get_train_batch, get_val_batch, vocab_size, enc, n_train_tokens = load_data(
            data_path, block_size, batch_size, device, encoding, retokenize=retokenize
        )
        model = GPT(config).to(device)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
        if ckpt.get("optimizer_state_dict") is not None:
            optimizer.load_state_dict(ckpt["optimizer_state_dict"])
            for st in optimizer.state.values():
                for k, v in st.items():
                    if isinstance(v, torch.Tensor):
                        st[k] = v.to(device)
    else:
        get_train_batch, get_val_batch, vocab_size, enc, n_train_tokens = load_data(
            data_path, block_size, batch_size, device, encoding, retokenize=retokenize
        )
        if tokens_per_param is not None:
            config, n_params = auto_config(vocab_size, block_size, n_train_tokens,
                                           tokens_per_param, n_layer=n_layer)
            n_layer = config.n_layer
            n_head = config.n_head
            n_embd = config.n_embd
            requested = n_train_tokens / tokens_per_param
            print(f"Auto-sized for {tokens_per_param:g} tokens/param "
                  f"(train tokens: {n_train_tokens:,}; requested ~{requested:,.0f} params, "
                  f"closest {n_layer}L/{n_head}H/{n_embd}D = {n_params:,} params)")
        else:
            n_layer = n_layer if n_layer is not None else 6
            n_embd = n_embd if n_embd is not None else 384
            config = GPTConfig(
                vocab_size=vocab_size,
                block_size=block_size,
                n_layer=n_layer,
                n_head=n_head,
                n_embd=n_embd,
            )
        model = GPT(config).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)

    actual = sum(p.numel() for p in model.parameters())
    print(f"Model: {config.n_layer}L/{config.n_head}H/{config.n_embd}D, "
          f"{actual / 1e6:.2f}M params, {n_train_tokens / actual:.3f} tokens/param")

    max_lr = 1e-3
    min_lr = max_lr * 0.1
    warmup_steps = 100

    if start_step >= max_steps:
        print(f"Already at step {start_step} >= max_steps {max_steps}. "
              f"Pass a larger --max_steps to continue training.")
        return model, enc

    def save_checkpoint(path, step):
        torch.save({
            "step": step,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "config": config,
            "encoding": enc.name,
            "loss_log": loss_log,
        }, path)
        with open("loss_log.json", "w") as f:
            json.dump(loss_log, f)

    pbar = tqdm(range(start_step, max_steps), desc="Training",
                total=max_steps, initial=start_step)
    for step in pbar:
        # --- validation loss ---
        if step % 100 == 0:
            model.eval()
            with torch.no_grad():
                val_losses = []
                for _ in range(20):
                    x, y = get_val_batch()
                    _, loss = model(x, y)
                    val_losses.append(loss.item())
                val_loss = sum(val_losses) / len(val_losses)
                tqdm.write(f"Step {step:5d} | val loss: {val_loss:.4f}")
            model.train()

        # --- update learning rate ---
        lr = get_lr(step, warmup_steps, max_steps, max_lr, min_lr)
        for param_group in optimizer.param_groups:
            param_group["lr"] = lr

        # --- training step ---
        x, y = get_train_batch()
        _, loss = model(x, y)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        pbar.set_postfix(loss=f"{loss.item():.4f}", lr=f"{lr:.2e}")

        # --- log loss ---
        loss_log["steps"].append(step)
        loss_log["train"].append(loss.item())
        if step % 100 == 0:
            loss_log["val"].append(val_loss)

        # --- generate sample ---
        if step > 0 and step % 100 == 0:
            model.eval()
            sample = generate(model, "Once upon a time ", enc,
                            max_new_tokens=100, temperature=0.8)
            tqdm.write(f"\n--- Step {step} sample ---\n{sample}\n---\n")
            model.train()

        # --- save resumable checkpoint ---
        if step > 0 and step % 1000 == 0:
            save_checkpoint("checkpoint_latest.pt", step)

    # --- save final checkpoint and loss log ---
    save_checkpoint("checkpoint_final.pt", max_steps)
    return model, enc
    
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train a tiny GPT")
    parser.add_argument("data_path", nargs="?", default="./data/shakespeare.txt",
                        help="Path to a training text file or a folder of text files")
    parser.add_argument("--tokens_per_param", type=float, default=None,
                        help="Auto-size the model so train_tokens/params ~ this ratio "
                             "(e.g. 20 = Chinchilla-optimal). Overrides --n_layer/--n_head/--n_embd; "
                             "n_head is derived from head_dim=64.")
    parser.add_argument("--n_layer", type=int, default=None,
                        help="Number of transformer blocks (default 6; in auto mode, pins depth)")
    parser.add_argument("--n_head", type=int, default=6, help="Number of attention heads (default 6)")
    parser.add_argument("--n_embd", type=int, default=None, help="Embedding dimension (default 384)")
    parser.add_argument("--block_size", type=int, default=256, help="Context window length")
    parser.add_argument("--batch_size", type=int, default=64, help="Training batch size")
    parser.add_argument("--max_steps", type=int, default=5000, help="Number of optimizer steps")
    parser.add_argument("--encoding", default="gpt2", help="tiktoken encoding name")
    parser.add_argument("--retokenize", action="store_true",
                        help="Force re-tokenizing the corpus even if a .tokens.bin cache exists")
    parser.add_argument("--resume", default=None,
                        help="Resume training from a checkpoint (e.g. checkpoint_latest.pt). "
                             "Architecture comes from the checkpoint; pass a larger --max_steps "
                             "to extend training.")
    args = parser.parse_args()

    train(
        args.data_path,
        max_steps=args.max_steps,
        batch_size=args.batch_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd,
        block_size=args.block_size,
        encoding=args.encoding,
        tokens_per_param=args.tokens_per_param,
        retokenize=args.retokenize,
        resume=args.resume,
    )
