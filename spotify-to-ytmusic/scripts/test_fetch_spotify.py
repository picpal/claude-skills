"""fetch_spotify.py의 순수 함수 단위 테스트.

네트워크를 쓰지 않는다. embed 페이지의 __NEXT_DATA__ 구조를 픽스처로 재현한다.
"""

import json

import pytest

from fetch_spotify import (
    EMBED_TRACK_CAP,
    PlaylistParseError,
    extract_playlist_id,
    parse_embed,
    parse_track_list,
)

# 실측 공유 URL (쿼리스트링이 길게 붙는 형태)
SHARE_URL = (
    "https://open.spotify.com/playlist/46WRCRFym2ofhc5l72Tf6B"
    "?si=2hSEqumsTmS2tjXEgD1q_g&utm_source=native-share-menu&pi=B-dpVXgaTzGA0&nd=1"
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (
            "https://open.spotify.com/playlist/46WRCRFym2ofhc5l72Tf6B",
            "46WRCRFym2ofhc5l72Tf6B",
        ),
        (SHARE_URL, "46WRCRFym2ofhc5l72Tf6B"),
        ("spotify:playlist:46WRCRFym2ofhc5l72Tf6B", "46WRCRFym2ofhc5l72Tf6B"),
        ("46WRCRFym2ofhc5l72Tf6B", "46WRCRFym2ofhc5l72Tf6B"),
        ("내 플레이리스트", None),
        ("", None),
        ("https://open.spotify.com/album/46WRCRFym2ofhc5l72Tf6B", None),
    ],
)
def test_extract_playlist_id(value, expected):
    assert extract_playlist_id(value) == expected


def _item(track_id="64LDTMmwjwpI416zpQbIRt", title="Flowerpot (Bonus Track)",
          subtitle="Alex", duration=265653, uri=None):
    return {
        "uri": uri if uri is not None else f"spotify:track:{track_id}",
        "title": title,
        "subtitle": subtitle,
        "duration": duration,
        "entityType": "track",
    }


def _html(track_list, name="밍밍 茶차2", uri="spotify:playlist:46WRCRFym2ofhc5l72Tf6B"):
    """실제 embed 페이지 구조를 최소한으로 재현한다."""
    payload = {
        "props": {
            "pageProps": {
                "state": {
                    "data": {
                        "entity": {
                            "type": "playlist",
                            "name": name,
                            "title": name,
                            "uri": uri,
                            "subtitle": "studiomingming",
                            "trackList": track_list,
                        }
                    }
                }
            }
        }
    }
    body = json.dumps(payload, ensure_ascii=False)
    return (
        '<html><body><script id="__NEXT_DATA__" type="application/json">'
        f"{body}</script></body></html>"
    )


def test_parse_track_list_maps_embed_fields():
    tracks, skipped = parse_track_list([_item()])
    assert skipped == 0
    assert tracks == [
        {
            "id": "64LDTMmwjwpI416zpQbIRt",
            "title": "Flowerpot (Bonus Track)",
            "artists": ["Alex"],
            "duration_ms": 265653,
        }
    ]


def test_parse_track_list_splits_multiple_artists():
    tracks, _ = parse_track_list(
        [_item(subtitle="Thierry Ganz, Cézanne, Uevo, Superfuse, Prime8")]
    )
    assert tracks[0]["artists"] == [
        "Thierry Ganz",
        "Cézanne",
        "Uevo",
        "Superfuse",
        "Prime8",
    ]


def test_parse_track_list_skips_non_tracks_and_untitled():
    tracks, skipped = parse_track_list(
        [
            _item(uri="spotify:episode:abc"),  # 팟캐스트 에피소드
            _item(title=""),  # 제목 없음
            "not-a-dict",
            _item(track_id="keepme", title="OK"),
        ]
    )
    assert skipped == 3
    assert [t["id"] for t in tracks] == ["keepme"]


def test_parse_track_list_handles_empty():
    assert parse_track_list([]) == ([], 0)
    assert parse_track_list(None) == ([], 0)


def test_parse_embed_reads_playlist_metadata():
    result = parse_embed(_html([_item()]))
    assert result["playlist_id"] == "46WRCRFym2ofhc5l72Tf6B"
    assert result["playlist_name"] == "밍밍 茶차2"
    assert len(result["tracks"]) == 1
    assert result["truncated"] is False


def test_parse_embed_flags_truncation_at_cap():
    """embed는 100곡에서 잘린다. 조용히 넘어가면 곡이 빠진 줄 모른다."""
    result = parse_embed(_html([_item(track_id=f"id{i:018d}") for i in range(EMBED_TRACK_CAP)]))
    assert len(result["tracks"]) == EMBED_TRACK_CAP
    assert result["truncated"] is True


def test_parse_embed_raises_without_next_data():
    with pytest.raises(PlaylistParseError):
        parse_embed("<html><body>no script here</body></html>")


def test_parse_embed_raises_without_track_list():
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{}}}</script>'
    )
    with pytest.raises(PlaylistParseError):
        parse_embed(html)


def test_parse_embed_raises_on_broken_json():
    html = '<script id="__NEXT_DATA__" type="application/json">{not json</script>'
    with pytest.raises(PlaylistParseError):
        parse_embed(html)


def test_parse_embed_survives_structure_change_around_entity():
    """경로가 바뀌어도 trackList만 있으면 계속 동작해야 한다."""
    payload = {
        "some": {"new": {"wrapper": {
            "uri": "spotify:playlist:abc",
            "name": "X",
            "trackList": [_item()],
        }}}
    }
    html = (
        '<script id="__NEXT_DATA__" type="application/json">'
        f"{json.dumps(payload)}</script>"
    )
    assert parse_embed(html)["playlist_name"] == "X"
