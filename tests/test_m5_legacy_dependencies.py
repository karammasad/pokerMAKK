"""Teammate policies keep the M5 snapshot they were built and tested against."""
import importlib


def test_teammate_policies_keep_classic_m5_dependency():
    classic = importlib.import_module('bots.m5_classic.bot')
    for module_name, attribute in (
        ('m6_safeadapt', 'anchor'), ('m8_bayes_types', 'anchor'),
        ('m9_cfrplus', 'fallback'), ('m10_seq_cfr', 'fallback'),
        ('m11_chosen', 'anchor'), ('m7_cherki', 'm5'),
    ):
        module = importlib.import_module(f'bots.{module_name}.bot')
        assert getattr(module, attribute) is classic, module_name
