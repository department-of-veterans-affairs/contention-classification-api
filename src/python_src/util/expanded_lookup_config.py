"""
This file contains constants and configurations for the expanded lookup table.
Parameters
----------
COMMON_WORDS: list[str]
    List of words to remove from incoming text and lookup table values.
MUSCULOSKELETAL_LUT: dict
    Lookup table for musculoskeletal conditions.
FILE_READ_HELPER: dict
    Helper dictionary that has the filepath and column names for instantiating the lookup table
"""

import os

from .table_versions import CONDITION_DROPDOWN_TABLE_VERSION

FILE_READ_HELPER = {
    'filepath': os.path.join(
        os.path.dirname(__file__),
        'data',
        'condition_dropdown_lookup_table',
        f'[Release notes] Contention Text to Classification mapping release notes - Contention Text Lookup '
        f'{CONDITION_DROPDOWN_TABLE_VERSION}.csv',
    ),
    'contention_text': 'CONTENTION TEXT',
    'classification_code': 'CLASSIFICATION CODE',
    'classification_name': 'CLASSIFICATION TEXT',
}

MUSCULOSKELETAL_LUT = {
    'knee': {
        'classification_code': 8997,
        'classification_name': 'Musculoskeletal - Knee',
    },
    'ankle': {
        'classification_code': 8991,
        'classification_name': 'Musculoskeletal - Ankle',
    },
    'hip': {
        'classification_code': 8996,
        'classification_name': 'Musculoskeletal - Hip',
    },
    'elbow': {
        'classification_code': 8993,
        'classification_name': 'Musculoskeletal - Elbow',
    },
    'shoulder': {
        'classification_code': 9002,
        'classification_name': 'Musculoskeletal - Shoulder',
    },
    'wrist': {
        'classification_code': 9004,
        'classification_name': 'Musculoskeletal - Wrist',
    },
    'low back': {
        'classification_code': 8998,
        'classification_name': 'Musculoskeletal - Mid/Lower Back (Thoracolumbar Spine)',
    },
    'lower back': {
        'classification_code': 8998,
        'classification_name': 'Musculoskeletal - Mid/Lower Back (Thoracolumbar Spine)',
    },
    'neck': {
        'classification_code': 8999,
        'classification_name': 'Musculoskeletal - Neck/Upper Back (Cervical Spine)',
    },
    'mid back': {
        'classification_code': 8998,
        'classification_name': 'Musculoskeletal - Mid/Lower Back (Thoracolumbar Spine)',
    },
    'upper back': {
        'classification_code': 8999,
        'classification_name': 'Musculoskeletal - Neck/Upper Back (Cervical Spine)',
    },
    'foot': {
        'classification_code': 8994,
        'classification_name': 'Musculoskeletal - Foot',
    },
    'toe': {
        'classification_code': 8994,
        'classification_name': 'Musculoskeletal - Foot',
    },
    'toes': {
        'classification_code': 8994,
        'classification_name': 'Musculoskeletal - Foot',
    },
    'feet': {
        'classification_code': 8994,
        'classification_name': 'Musculoskeletal - Foot',
    },
}

COMMON_WORDS = [
    'left',
    'right',
    'bilateral',
    'in',
    'of',
    'or',
    'the',
    'my',
    'and',
    'chronic',
    # 'lower',
    'to',
    'and',
    'major',
    'than',
    'with',
    # 'upper',
    # 'low',
    'a',
    'va',
    'for',
    'as',
    'has',
    'me',
    'one',
    'use',
    'year',
    'within',
    'worse',
    'at',
    'have',
    'side',
    'by',
    'frequent',
    'mild',
    'loud',
    'weak',
    'bl',
    # 'not',
    'exam',
    'undiagnosed',
    'during',
    'is',
    'when',
    'day',
    'was',
    'all',
    'aircraft',
    'total',
    'moderate',
    'noises',
    'complete',
    'after',
    'up',
    'it',
    'bi',
    'daily',
    'no',
    'had',
    'getting',
    'also',
    'rt',
    'sp',
    'be',
    'see',
    'need',
    'an',
    'which',
    'since',
    'this',
    'jet',
    "can't",
    'cant',
    'pain',
    'condition',
]
