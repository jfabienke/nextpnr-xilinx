# UltraScale+ routing smoke tests

These tests synthesize, place, and route an IO passthrough and a LUT/FF design
with a fixed seed. Both routers must complete, router2 must report zero overuse,
and every FASM must contain an `INT_X*Y*` routing feature. The final graph check
also requires 3,774 physical PIPs and 722 muxes on one loaded INT tile (the four
bidirectional physical PIPs expand to 3,778 directed nextpnr arcs).

Generate a chipdb using the commands in the repository root README, then run:

```sh
python3 xilinx/tests/routing-smoke/run.py \
  --device xczu2cg --chipdb build/xczu2cg.bin \
  --nextpnr build/nextpnr-xilinx
```

Use `--device xcvu33p` with an `xcvu33p.bin` chipdb for the VU33P test. The
harness reports the number of unprocessed route-throughs separately because
they do not invalidate routing or INT-PIP FASM. Add `--require-clean-route-thrus`
for the stricter hardware-readiness gate. Generated JSON, FASM, chipdb, and
RapidWright data stay outside the source tree and must not be committed.
