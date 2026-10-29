"""Versioned reconstruction contract. Does not confuse inferred behavior with observations."""
from copy import deepcopy

def specification(evidence, output):
    nodes=deepcopy(evidence['nodes'])
    return {'schema':'veyra-reconstruction/2','format':output,
        'coordinateSystem':'source viewport CSS pixels; root-relative crop',
        'viewport':evidence.get('viewport'), 'root':nodes[0]['id'],
        'nodes':nodes,'hover':evidence.get('hover'),'paintContext':evidence.get('visualContext'),
        'responsiveObservations':{'capturedViewports':[evidence.get('viewport')],'breakpoints':'unknown; do not invent observations'},
        'coverage':{'truncated':evidence.get('truncated',False),'included':len(nodes)},
        'requirements':['Reconstruct, do not redesign. Retain measured colors, type and parent-child layout.',
            'Preserve data-veyra-node IDs on corresponding DOM elements for comparison.',
            'Keep flex/grid; do not flatten into arbitrary absolute-positioned cards.',
            'Use only embedded safe assets; missing assets must remain explicitly marked.',
            'Do not invent routes, backend actions, menus or scroll behavior without evidence.']}
