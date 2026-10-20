# 01 · Client brief

*Simulated engagement. The client, people and numbers in this section are invented to frame the work; everything after it (requirements, code, evaluation results) is real and reproducible.*

## Who

A lab-automation team (six engineers) supporting about forty research groups that control instruments from Python with PyVISA: power meters, oscilloscopes, multimeters, lasers over GPIB, USB, serial and Ethernet.

## The problem, in their words

> "Half our tickets are the same ten questions. Timeouts, termination characters, 'could not find VISA library', resource strings, reading binary data. The answers are all in the PyVISA docs, but people don't find them, and when a junior engineer answers from memory they're sometimes wrong. We tried a general chatbot: it was fluent and confidently invented methods that don't exist."

## What they asked for

1. An assistant that answers PyVISA questions **only from the official documentation**, and shows where each answer comes from.
2. It must **say so when the documentation doesn't cover a question**, instead of guessing.
3. It should be able to **read a live instrument** for the most common check ("is the power meter talking, and what does it read?").
4. It must run **on their own hardware** (no lab data leaves the building), and they want to know what it would cost if they moved it to a hosted model.
5. They need to **trust it before rollout**: a measurable quality bar, and a way to know if a change makes it worse.

## Constraints

- On-premises model server (they already run llama.cpp); a hosted model is a possible later option.
- Answers in under 10 seconds for a support chat.
- Documentation version pinned to the PyVISA release they use (1.16.2).
- The team's engineers will maintain it after handover: plain Python, small, documented.

## Success, as they would judge it

- Fewer repeated tickets; nobody acting on an invented answer.
- A one-page report they can show their manager: how often it is right, how often it cites correctly, how fast, how much it costs.
