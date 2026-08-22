# WillsitoGG Raikopon tuning

This directory contains only the current WillsitoGG Raikopon SD Path_v3 tuning material.

The current tune is intentionally represented as a reproducible binary patch, because a reliable source-level equivalent was not established. `patch-raikopon-sdpath-v3.py` applies the exact current change to the official Raikopon v2.5.0 NRO: the compiled default user-data root changes from `sdmc:/switch/azahar/` to `sdmc:/switch/raikopon/` while argv/direct-forwarder logic remains upstream.

The current installable `raikopon.nro` is published in this fork's GitHub Releases. Historical v1/v2 material is intentionally not retained.
