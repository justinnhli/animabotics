"""Tests for probabilities.py."""

from fractions import Fraction

from animabotics.probabilities import DiscreteDistribution


def test_discrete_distribution():
    # type: () -> None
    """Test DiscreteDistribution."""
    fair_coin = DiscreteDistribution({
        'head': Fraction(1, 2),
        'tail': Fraction(1, 2),
    })
    bias_coin = DiscreteDistribution({
        'head': Fraction(1, 3),
        'tail': Fraction(2, 3),
    })
    head_coin = bias_coin.condition(lambda value: value == 'head')
    assert len(bias_coin) == 2
    assert len(head_coin) == 1
    assert bias_coin['head'] == Fraction(1, 3)
    assert bias_coin['tail'] == Fraction(2, 3)
    assert bias_coin['none'] == 0
    assert bias_coin == bias_coin # pylint: disable = comparison-with-itself
    assert bias_coin != fair_coin
    assert bias_coin.values_set == set(['head', 'tail'])
    assert head_coin.values_set == set(['head'])
    assert set(bias_coin) == set(['head', 'tail'])
    assert str(bias_coin) == 'head:0.333 tail:0.667'
    pair_coin = bias_coin.cross(bias_coin)
    assert len(pair_coin) == 4
    assert pair_coin.values_set == set([
        ('head', 'head'),
        ('head', 'tail'),
        ('tail', 'head'),
        ('tail', 'tail'),
    ])
    assert (
        set(probability for _, probability in pair_coin.probabilities)
        == set([Fraction(1, 9), Fraction(2, 9), Fraction(4, 9)])
    )
    str_pair_coin = pair_coin.map_values(
        lambda pair: ''.join(sorted(value[0] for value in pair)).upper()
    )
    assert len(str_pair_coin) == 3
    assert str_pair_coin.values_set == set(['HH', 'HT', 'TT'])
    assert str(str_pair_coin) == 'HH:0.111 HT:0.444 TT:0.444'
