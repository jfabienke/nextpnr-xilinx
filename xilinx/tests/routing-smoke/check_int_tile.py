import os

sample_tile = os.environ["INT_TILE"]
tile_wires = {
    wire
    for wire in ctx.getWires()
    if wire.startswith(f"{sample_tile}/") and "PSEUDO_" not in wire
}
muxes = {}
for wire in tile_wires:
    uphill = tuple(ctx.getPipsUphill(wire))
    if uphill:
        muxes[wire] = uphill

directed_pips = {str(pip) for pips in muxes.values() for pip in pips}
physical_pips = {
    tuple(sorted(pip_name.split("->", 1)))
    for pip_name in directed_pips
}
print(
    f"INT_GRAPH tile={sample_tile} physical_pips={len(physical_pips)} "
    f"directed_arcs={len(directed_pips)} muxes={len(muxes)}"
)
assert len(physical_pips) == 3774
assert len(muxes) == 722
