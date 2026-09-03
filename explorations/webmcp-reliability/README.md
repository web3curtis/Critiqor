# Critiqor × Crema reliability experiment

A public, Codex-desktop-style presentation of a controlled WebMCP reliability experiment using the genuine Crema & Co. target and two genuine anonymous Critiqor dashboards.

Live judge experience: <https://critiqor-crema-reliability.terrence-qiu-7311.chatgpt.site/?agent-playback=1>

- Baseline: a public anonymous Critiqor run marked Not Ready For Production, with its run-specific playbook.
- Playbook-guided: a public anonymous Critiqor run marked Production Ready.
- Target in both rows: a deterministic, signed-in Crema judge session with exactly one white Lelit Bianca V3 in the cart and checkout disabled.

The page then limits the narrative to the exact experiment, findings, and comparison. In five matched GPT-5.4-mini/medium pairs, blind redispatch and duplicate cart peaks fell from 2/5 to 0/5 while task success stayed 5/5. Speed, tool-call count, and token cost did not improve.

Each run repeats the exact agent task beside its heading. The playbook-guided prompt also names `public/evidence/improvement_playbook.md` and tells the agent to apply it. “Watch agent run” begins in the genuine Crema Catalog, plays a labelled Codex-style pointer simulation, then clicks Compare and renders the arm-specific result inside Crema itself. “Skip to final result” immediately opens that populated Compare state. Baseline playback includes the duplicate peak and repair, while improved playback reconciles before retrying.

The six experiment and findings cards retain their solid original presentation and open into large detail dialogs over a blurred page. In the comparison table, the first four rows link to their related Critiqor views; the final three cost rows intentionally remain static.

Five WebMCP tools use the same finalized manifest and visible playback as the human interface. Four inspect the experiment evidence, method, playbook, and sealed runs; `show_critiqor_experiment_arm` visibly opens, replays, or resets either experiment arm.

## Judge quickstart

1. Open the live URL in ChatGPT's in-app browser, or in Chrome 149+ with `chrome://flags/#enable-webmcp-testing` enabled.
2. Ask the agent: **“Show the improved run, then explain why it is safer.”**
3. Confirm that the improved Crema frame opens the final Compare result with exactly one white Lelit Bianca V3 and no checkout.
4. Compare it with the baseline frame and use the linked Critiqor evidence, playbook, and dashboards.

No login, local service, private file path, API key, or purchase is required for judging. Run `npm run sync:evidence` to refresh the sanitized public artifacts and anonymous dashboard resources.
