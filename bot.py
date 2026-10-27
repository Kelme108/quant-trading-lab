"""Exemplo educacional de bot de trading em modo paper trading.

A estratégia usa o cruzamento de duas médias móveis simples (SMA):
- compra quando a SMA curta cruza acima da SMA longa;
- vende quando a SMA curta cruza abaixo da SMA longa.

O script não se conecta a uma corretora e não envia ordens reais.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Position:
    quantity: float = 0.0
    entry_price: float = 0.0


@dataclass
class PaperBroker:
    cash: float = 1_000.0
    fee_rate: float = 0.001  # 0,1% por operação
    position: Position = field(default_factory=Position)

    def buy_all(self, price: float) -> None:
        if self.position.quantity > 0 or self.cash <= 0:
            return

        fee = self.cash * self.fee_rate
        amount_to_invest = self.cash - fee
        self.position = Position(
            quantity=amount_to_invest / price,
            entry_price=price,
        )
        self.cash = 0.0
        print(f"COMPRA  preço={price:8.2f} quantidade={self.position.quantity:.6f}")

    def sell_all(self, price: float) -> None:
        if self.position.quantity <= 0:
            return

        gross = self.position.quantity * price
        fee = gross * self.fee_rate
        self.cash = gross - fee
        print(f"VENDA   preço={price:8.2f} quantidade={self.position.quantity:.6f}")
        self.position = Position()

    def equity(self, price: float) -> float:
        return self.cash + self.position.quantity * price


def sma(values: list[float], window: int) -> float | None:
    """Calcula a média móvel simples da janela mais recente."""
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def run_bot(prices: Iterable[float], short_window: int = 3, long_window: int = 5) -> None:
    if short_window >= long_window:
        raise ValueError("short_window deve ser menor que long_window")

    broker = PaperBroker()
    history: list[float] = []
    previous_short: float | None = None
    previous_long: float | None = None

    for step, price in enumerate(prices, start=1):
        if price <= 0:
            raise ValueError("Os preços devem ser positivos")

        history.append(price)
        current_short = sma(history, short_window)
        current_long = sma(history, long_window)
        print(
            f"tick={step:02d} preço={price:8.2f} "
            f"SMA{short_window}={current_short if current_short else '-':>8} "
            f"SMA{long_window}={current_long if current_long else '-':>8}"
        )

        if current_short is None or current_long is None:
            continue

        crossed_up = (
            previous_short is not None
            and previous_long is not None
            and previous_short <= previous_long
            and current_short > current_long
        )
        crossed_down = (
            previous_short is not None
            and previous_long is not None
            and previous_short >= previous_long
            and current_short < current_long
        )

        if crossed_up:
            broker.buy_all(price)
        elif crossed_down:
            broker.sell_all(price)

        previous_short = current_short
        previous_long = current_long

    last_price = history[-1]
    if broker.position.quantity > 0:
        broker.sell_all(last_price)

    print(f"Saldo final: R$ {broker.cash:.2f}")
    print(f"Resultado:   R$ {broker.cash - 1_000.0:+.2f}")


if __name__ == "__main__":
    # Série pequena apenas para demonstrar o funcionamento localmente.
    sample_prices = [100, 99, 98, 97, 98, 100, 103, 105, 102, 99, 96, 98, 101]
    run_bot(sample_prices)
