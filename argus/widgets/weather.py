"""WeatherWidget — weather display using the open-meteo API (no key required)."""

from __future__ import annotations

from rich.markup import escape as mu_escape
from textual import work
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class WeatherWidget(Widget):
    """Weather widget using the open-meteo API.

    Reads ``app.argus_config.city`` for the location (defaults to "London").
    Refreshes automatically every 30 minutes.
    """

    DEFAULT_CSS = """
    WeatherWidget {
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    _content: reactive[str] = reactive("Loading weather...")

    # ── Compose / mount ───────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static("", id="weather-content")

    def on_mount(self) -> None:
        self._fetch_weather()
        self.set_interval(1800.0, self._fetch_weather)  # refresh every 30 min

    # ── Reactive watcher ──────────────────────────────────────────────────────

    def watch__content(self, val: str) -> None:
        try:
            self.query_one("#weather-content", Static).update(val)
        except Exception:
            pass

    # ── Data fetching ─────────────────────────────────────────────────────────

    @work(exclusive=True)
    async def _fetch_weather(self) -> None:
        """Fetch geocoding + forecast data from open-meteo and update the display."""
        import httpx

        cfg = getattr(self.app, "argus_config", None)
        city_name: str = cfg.city if cfg is not None else "London"

        _timeout = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)
        try:
            async with httpx.AsyncClient(timeout=_timeout) as client:
                # ── Geocoding ────────────────────────────────────────────────
                geo_resp = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": city_name,
                        "count": 1,
                        "language": "en",
                        "format": "json",
                    },
                )
                geo_data = geo_resp.json()
                results = geo_data.get("results", [])
                if not results:
                    self._content = f"[yellow]City not found: {city_name}[/]"
                    return

                lat = results[0]["latitude"]
                lon = results[0]["longitude"]
                name = results[0].get("name", city_name)

                # ── Forecast ─────────────────────────────────────────────────
                weather_resp = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": (
                            "temperature_2m,weathercode,"
                            "windspeed_10m,relative_humidity_2m"
                        ),
                        "daily": (
                            "temperature_2m_max,temperature_2m_min,weathercode"
                        ),
                        "forecast_days": 3,
                        "timezone": "auto",
                    },
                )
                data = weather_resp.json()

            current = data.get("current", {})
            daily = data.get("daily", {})

            temp = current.get("temperature_2m", "?")
            code = current.get("weathercode", 0)
            wind = current.get("windspeed_10m", 0)
            humidity = current.get("relative_humidity_2m", 0)

            icon = _weather_icon(code)
            desc = _weather_desc(code)

            lines: list[str] = [
                f"[bold]{icon} {name}[/]",
                f"[bold primary]{temp}°C[/]  {desc}",
                f"[dim]💨 {wind} km/h  💧 {humidity}%[/]",
                "",
                "[dim]Forecast:[/]",
            ]

            times: list[str] = daily.get("time", [])
            maxs: list = daily.get("temperature_2m_max", [])
            mins: list = daily.get("temperature_2m_min", [])
            codes: list = daily.get("weathercode", [])

            for i in range(min(3, len(times))):
                day_icon = _weather_icon(codes[i] if i < len(codes) else 0)
                max_t = maxs[i] if i < len(maxs) else "?"
                min_t = mins[i] if i < len(mins) else "?"
                lines.append(
                    f"  {times[i]}  {day_icon} {max_t}° / {min_t}°"
                )

            self._content = "\n".join(lines)

        except Exception as exc:
            self._content = f"[yellow]Weather unavailable[/]\n[dim]{mu_escape(str(exc))}[/]"


# ── WMO weather-code look-up tables ──────────────────────────────────────────

_WMO_ICONS: dict[int, str] = {
    0: "☀️",
    1: "🌤",
    2: "⛅",
    3: "☁️",
    45: "🌫",
    51: "🌦",
    61: "🌧",
    71: "🌨",
    80: "🌦",
    95: "⛈",
}

_WMO_DESC: dict[int, str] = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    51: "Drizzle",
    61: "Rain",
    71: "Snow",
    80: "Showers",
    95: "Thunderstorm",
}


def _weather_icon(code: int) -> str:
    """Return the closest WMO icon for a weather code."""
    for k in sorted(_WMO_ICONS.keys(), reverse=True):
        if code >= k:
            return _WMO_ICONS[k]
    return "🌡"


def _weather_desc(code: int) -> str:
    """Return the closest WMO description for a weather code."""
    for k in sorted(_WMO_DESC.keys(), reverse=True):
        if code >= k:
            return _WMO_DESC[k]
    return "Unknown"
