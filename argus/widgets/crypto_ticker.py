import httpx

_HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive
from textual import work

COINS = ["bitcoin", "ethereum", "solana", "cardano", "polkadot"]


class CryptoTickerWidget(Widget):
    """Crypto price ticker using CoinGecko free API."""

    DEFAULT_CSS = """
    CryptoTickerWidget {
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    _content: reactive[str] = reactive("Loading prices...")

    def compose(self) -> ComposeResult:
        yield Static("", id="crypto-content")

    def on_mount(self) -> None:
        self._fetch()
        self.set_interval(60.0, self._fetch)  # refresh every minute

    def watch__content(self, val: str) -> None:
        try:
            self.query_one("#crypto-content", Static).update(val)
        except Exception:
            pass

    @work(exclusive=True)
    async def _fetch(self) -> None:
        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                resp = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": ",".join(COINS),
                        "vs_currencies": "usd",
                        "include_24hr_change": "true",
                    }
                )
                data = resp.json()
                lines = ["[bold]Crypto Prices[/]", ""]
                for coin in COINS:
                    if coin not in data:
                        continue
                    price = data[coin].get("usd", 0)
                    change = data[coin].get("usd_24h_change", 0)
                    color = "green" if change >= 0 else "red"
                    sign = "+" if change >= 0 else ""
                    lines.append(
                        f"[bold]{coin[:3].upper()}[/] "
                        f"${price:,.2f} "
                        f"[{color}]{sign}{change:.2f}%[/]"
                    )
                self._content = "\n".join(lines)
        except Exception as e:
            self._content = f"[yellow]Prices unavailable[/]\n[dim]{e}[/]"
