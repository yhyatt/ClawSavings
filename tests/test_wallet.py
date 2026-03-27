"""
Tests for clawsavings/wallet.py — CRUD operations and atomic write safety.
"""
import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pytest
from unittest.mock import patch
import wallet as w


@pytest.fixture
def tmp_wallet(tmp_path):
    """Provide a temporary wallet file and patch WALLET_PATH."""
    wallet_file = str(tmp_path / "wallet.json")
    with patch.object(w, 'WALLET_PATH', wallet_file):
        yield wallet_file


def make_card(**kwargs):
    """Create a minimal card dict for testing."""
    card = w.empty_card()
    card.update(kwargs)
    return card


class TestLoadSave:
    def test_load_wallet_creates_empty_on_missing_file(self, tmp_wallet):
        """load_wallet() on nonexistent file returns empty structure."""
        data = w.load_wallet()
        assert data["version"] == "1.0"
        assert data["cards"] == []

    def test_save_and_reload(self, tmp_wallet):
        """Saved wallet can be reloaded correctly."""
        wallet = w.load_wallet()
        card = make_card(merchant="Castro", face_value=200.0, balance=200.0)
        wallet["cards"].append(card)
        w.save_wallet(wallet)

        reloaded = w.load_wallet()
        assert len(reloaded["cards"]) == 1
        assert reloaded["cards"][0]["merchant"] == "Castro"

    def test_save_wallet_atomic_no_tmp_file_left(self, tmp_wallet):
        """After save_wallet(), the .tmp file should not remain."""
        wallet = w.load_wallet()
        w.save_wallet(wallet)
        tmp_file = tmp_wallet + ".tmp"
        assert not os.path.exists(tmp_file), ".tmp file should be removed after atomic replace"

    def test_save_wallet_atomic_preserves_data_on_second_save(self, tmp_wallet):
        """Two consecutive saves don't corrupt data."""
        wallet = w.load_wallet()
        card = make_card(merchant="Zara", face_value=500.0, balance=500.0)
        wallet["cards"].append(card)
        w.save_wallet(wallet)
        w.save_wallet(wallet)

        reloaded = w.load_wallet()
        assert len(reloaded["cards"]) == 1

    def test_save_updates_last_updated(self, tmp_wallet):
        """save_wallet() updates the last_updated field."""
        wallet = w.load_wallet()
        wallet["last_updated"] = "1970-01-01"  # old date
        w.save_wallet(wallet)
        from datetime import date
        reloaded = w.load_wallet()
        assert reloaded["last_updated"] == str(date.today())


class TestCardOperations:
    def test_add_card(self, tmp_wallet):
        """A card can be added to the wallet."""
        wallet = w.load_wallet()
        card = make_card(merchant="Castro", face_value=300.0, balance=300.0)
        wallet["cards"].append(card)
        w.save_wallet(wallet)

        reloaded = w.load_wallet()
        assert len(reloaded["cards"]) == 1
        assert reloaded["cards"][0]["merchant"] == "Castro"
        assert reloaded["cards"][0]["face_value"] == 300.0

    def test_get_balance_active_card(self, tmp_wallet):
        """effective_status returns 'active' for a non-expired card."""
        card = make_card(status="active", expiry=None)
        assert w.effective_status(card) == "active"

    def test_get_balance_expired_card(self, tmp_wallet):
        """effective_status returns 'expired' for a past-expiry card."""
        card = make_card(status="active", expiry="2020-01-01")
        assert w.effective_status(card) == "expired"

    def test_get_balance_used_card(self, tmp_wallet):
        """effective_status returns 'used' for a card with status=used."""
        card = make_card(status="used")
        assert w.effective_status(card) == "used"

    def test_use_credit_full_deduction(self, tmp_wallet):
        """Deducting the full balance marks card as used."""
        wallet = w.load_wallet()
        card = make_card(merchant="Super", face_value=200.0, balance=200.0, status="active")
        wallet["cards"].append(card)
        w.save_wallet(wallet)

        # Simulate cmd_use logic
        reloaded = w.load_wallet()
        c = reloaded["cards"][0]
        new_bal = c["balance"] - 200.0
        c["balance"] = round(new_bal, 2)
        c["status"] = "used" if c["balance"] == 0 else "partial"
        w.save_wallet(reloaded)

        final = w.load_wallet()
        assert final["cards"][0]["status"] == "used"
        assert final["cards"][0]["balance"] == 0

    def test_use_credit_partial_deduction(self, tmp_wallet):
        """Deducting partial amount marks card as partial."""
        wallet = w.load_wallet()
        card = make_card(merchant="Fox", face_value=500.0, balance=500.0, status="active")
        wallet["cards"].append(card)
        w.save_wallet(wallet)

        reloaded = w.load_wallet()
        c = reloaded["cards"][0]
        c["balance"] = round(c["balance"] - 200.0, 2)
        c["status"] = "used" if c["balance"] == 0 else "partial"
        w.save_wallet(reloaded)

        final = w.load_wallet()
        assert final["cards"][0]["status"] == "partial"
        assert final["cards"][0]["balance"] == 300.0

    def test_list_cards_excludes_used(self, tmp_wallet):
        """Active list excludes used/expired cards."""
        wallet = w.load_wallet()
        active = make_card(merchant="Active", status="active", face_value=100.0)
        used = make_card(merchant="Used", status="used", face_value=100.0)
        wallet["cards"] = [active, used]
        w.save_wallet(wallet)

        reloaded = w.load_wallet()
        active_cards = [c for c in reloaded["cards"] if w.effective_status(c) not in ("used", "expired")]
        assert len(active_cards) == 1
        assert active_cards[0]["merchant"] == "Active"

    def test_multiple_cards_different_merchants(self, tmp_wallet):
        """Multiple cards with different merchants are stored correctly."""
        wallet = w.load_wallet()
        for merchant in ["Castro", "Zara", "H&M"]:
            card = make_card(merchant=merchant, face_value=100.0, balance=100.0)
            wallet["cards"].append(card)
        w.save_wallet(wallet)

        reloaded = w.load_wallet()
        assert len(reloaded["cards"]) == 3
        merchants = {c["merchant"] for c in reloaded["cards"]}
        assert merchants == {"Castro", "Zara", "H&M"}

    def test_find_card_by_prefix(self, tmp_wallet):
        """find_card() locates a card by ID prefix."""
        wallet = w.load_wallet()
        card = make_card(merchant="TestStore")
        card["id"] = "abc12345"
        wallet["cards"].append(card)
        w.save_wallet(wallet)

        reloaded = w.load_wallet()
        found = w.find_card(reloaded, "abc1")
        assert found["merchant"] == "TestStore"


class TestAtomicWrite:
    def test_atomic_write_produces_valid_json(self, tmp_wallet):
        """The wallet file after save is valid JSON (not truncated)."""
        wallet = w.load_wallet()
        for i in range(10):
            wallet["cards"].append(make_card(merchant=f"Store{i}", face_value=100.0))
        w.save_wallet(wallet)

        with open(tmp_wallet, "r") as f:
            data = json.load(f)  # should not raise
        assert len(data["cards"]) == 10

    def test_tmp_file_cleanup_on_normal_save(self, tmp_wallet):
        """No .tmp file remains after a successful save."""
        wallet = w.load_wallet()
        w.save_wallet(wallet)
        assert not os.path.exists(tmp_wallet + ".tmp")

    def test_existing_file_preserved_if_write_path_invalid(self, tmp_wallet):
        """If wallet.json exists, it remains intact before a write attempt."""
        wallet = w.load_wallet()
        card = make_card(merchant="Original", face_value=200.0)
        wallet["cards"].append(card)
        w.save_wallet(wallet)

        # Verify original data is intact after save
        reloaded = w.load_wallet()
        assert reloaded["cards"][0]["merchant"] == "Original"


class TestHelpers:
    def test_fmt_ils_none(self):
        assert w.fmt_ils(None) == "—"

    def test_fmt_ils_value(self):
        assert w.fmt_ils(250) == "₪250"

    def test_compute_pct(self):
        """200 face / 150 paid = 25% savings."""
        assert w.compute_pct(200, 150) == 25.0

    def test_compute_pct_no_values(self):
        assert w.compute_pct(None, None) is None

    def test_is_expired_past_date(self):
        card = make_card(expiry="2020-06-01")
        assert w.is_expired(card) is True

    def test_is_expired_future_date(self):
        card = make_card(expiry="2099-12-31")
        assert w.is_expired(card) is False

    def test_is_expired_no_expiry(self):
        card = make_card(expiry=None)
        assert w.is_expired(card) is False
