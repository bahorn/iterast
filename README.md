# Iterast

Small util to auto reload a python script, only rerunning code that occurs after
a changed section.
So basically its a REPL that reads from a file.

Evaluates the code in process!

[Video demo](https://youtu.be/FjP6IyULLFQ)

## Usage

Setup:
```
pip install -r requirements.txt
```

Run like so:
```
python3 iterast.py ./path/to/file.py
```

Optional flag is `--no-clear`, which will disable clearing the screen on reset.

You can trigger a reload with a `SIGQUIT`, which you can send by pressing
`CTRL+\`

## License

MIT
