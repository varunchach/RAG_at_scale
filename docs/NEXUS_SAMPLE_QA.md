# Nexus Sample Questions and Expected Answers

Use this document after ingesting `data/raw/nexus_research_bulletin_2025.pdf` into either app.

## Best Demo Questions

### 1. Who is Dr. Elara Vonn and what is ORIN-7?

Expected answer:

Dr. Elara Vonn is the lead researcher behind the Vonn Entropic Compression theory. `ORIN-7` is her `400-qubit photonic processor` used in `Halvard, Norway`.

### 2. Which scientist discovered the Mossad-Chen Fold, and what is its thermal stability?

Expected answer:

`Professor Tariq Mossad` discovered the `Mossad-Chen Fold`, and it remains stable up to `210 degrees C`.

### 3. What did FRAC-9 achieve in the benchmark results?

Expected answer:

`FRAC-9` ran a `70-billion-parameter language model` on a device with only `512 MB of RAM` at `18 tokens per second`, while preserving `96.3%` of the original accuracy on `NNBS-v4`.

### 4. What is HYDROS-1 and how efficient is it?

Expected answer:

`HYDROS-1` is a `room-temperature hydrogen fuel cell` invented by `Dr. Okafor Nweze`, and it achieves `91% efficiency` using a `bismuth-selenide membrane`.

### 5. Which city is called the Silicon Fjord, and what initiative reduced energy waste there?

Expected answer:

`Halvard, Norway` is called the `Silicon Fjord`, and the `Halvard Smart Grid Initiative` reduced energy waste there by `38%`.

## Good Entity-Rich Questions

### 6. Which city uses the Desalination Loop, and what percentage of wastewater does it recycle?

Expected answer:

`Aqaris, Jordan` uses the `Desalination Loop`, and it recycles `99.2%` of wastewater.

### 7. What is veltranite and why is it important?

Expected answer:

`Veltranite` is a rare earth mineral from `Veltran, Canada`. It becomes superconductive at `-18 degrees C` when doped with `3% osmium`, which makes it important for possible lossless power transmission.

### 8. What discovery won the Nexus Grand Prize 2025?

Expected answer:

The discovery was `VELT-OS3`, a form of `veltranite doped with 3% osmium` that achieved superconductivity at `-18 degrees C`. It won the `Nexus Grand Prize 2025`, worth `$5 million`.

### 9. What is MCF-S3 and where was it piloted?

Expected answer:

`MCF-S3` is a synthetic variant of the `Mossad-Chen Fold` protein that can remove `PFAS chemicals` from water at `99.7% efficiency`. It was piloted at the `Aqaris Eastern Reservoir`.

### 10. Who pioneered Neuromorphic Fractal Encoding, and where was it deployed?

Expected answer:

`Dr. Senna Brightwell` pioneered `Neuromorphic Fractal Encoding (NFE)`, and her startup `BrightCore AI` deployed it across `47 countries` by `2024`.

## Strong Multi-Hop Questions

### 11. Which city hosts the lab of the Bramwell Prize winner, and what machine does that lab use?

Expected answer:

The city is `Halvard, Norway`, and the lab uses `ORIN-7`, a `400-qubit photonic processor`.

### 12. Which finding could enable lossless transcontinental power transmission, and what exact material change made it possible?

Expected answer:

`FINDING NX-005` could enable lossless transcontinental power transmission. It used `veltranite doped with 3% osmium`, codenamed `VELT-OS3`.

### 13. Which scientist worked on deep-sea proteins, and what industrial use came from that work?

Expected answer:

`Professor Tariq Mossad` worked on deep-sea proteins, and that work led to `MCF-S3`, which can neutralize `PFAS chemicals in water`.

### 14. Compare Elara Vonn's and Okafor Nweze's work in one answer.

Expected answer:

`Elara Vonn` worked on reversible entropy and quantum coherence using `ORIN-7`, while `Okafor Nweze` developed `HYDROS-1`, a high-efficiency room-temperature hydrogen fuel cell.

### 15. Which city hosts the Deep Ocean Data Centre, and which scientist there studied deep-sea protein structures?

Expected answer:

The city is `Aqaris, Jordan`, and the scientist is `Professor Tariq Mossad`.

## Nice Eval-Demo Questions

These are good questions for the eval app because they tend to generate clean retrieval evidence and easy-to-explain judge scores.

- `What is GraphRAG and how does it improve standard RAG?`
- `What did FRAC-9 achieve in the benchmark results?`
- `What discovery won the Nexus Grand Prize 2025?`

## Demo Tips

1. Ingest the Nexus PDF first.
2. Ask one direct factual question.
3. Ask one multi-hop question.
4. Show the answer and retrieved chunks.
5. Open the eval dashboard and CloudWatch logs to show judge scores.
