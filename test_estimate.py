"""
見積APIのテスト
"""
import pytest
from app import app
from logic.estimate import calculate_estimate


# logic/estimate.py のユニットテスト
class TestCalculateEstimate:
    """見積ロジックのテスト"""

    def test_normal_case_medium(self):
        """正常ケース: 12画面, medium"""
        # 12 × 120000 × 1.0 × 1.1 = 1,584,000
        result = calculate_estimate(12, "medium")
        assert result["estimated_amount"] == 1_584_000
        assert result["breakdown"]["base"] == 1_440_000
        assert result["breakdown"]["difficulty"] == 1.0
        assert result["breakdown"]["buffer"] == 1.1

    def test_boundary_case_low(self):
        """境界ケース: 1画面, low"""
        # 1 × 120000 × 0.8 × 1.1 = 105,600
        result = calculate_estimate(1, "low")
        assert result["estimated_amount"] == 105_600
        assert result["breakdown"]["base"] == 120_000
        assert result["breakdown"]["difficulty"] == 0.8

    def test_boundary_case_high(self):
        """境界ケース: 1画面, high"""
        # 1 × 120000 × 1.3 × 1.1 = 171,600
        result = calculate_estimate(1, "high")
        assert result["estimated_amount"] == 171_600
        assert result["breakdown"]["base"] == 120_000
        assert result["breakdown"]["difficulty"] == 1.3

    def test_unknown_complexity_defaults_to_medium(self):
        """不明な複雑度は1.0（medium相当）として扱う"""
        # 10 × 120000 × 1.0 × 1.1 = 1,320,000
        result = calculate_estimate(10, "unknown")
        assert result["estimated_amount"] == 1_320_000
        assert result["breakdown"]["difficulty"] == 1.0


# app.py のAPIテスト
class TestEstimateAPI:
    """見積APIのテスト"""

    @pytest.fixture
    def client(self):
        """Flaskテストクライアント"""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_estimate_success(self, client):
        """正常ケース: 12画面, medium"""
        response = client.post(
            "/estimate",
            json={"screen_count": 12, "complexity": "medium"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["estimated_amount"] == 1_584_000
        assert data["currency"] == "JPY"
        assert data["message"] is None
        # v1.1: breakdown フィールドの確認
        assert "breakdown" in data
        assert data["breakdown"]["base"] == 1_440_000
        assert data["breakdown"]["difficulty"] == 1.0
        assert data["breakdown"]["buffer"] == 1.1

    def test_estimate_low_complexity(self, client):
        """境界ケース: 1画面, low"""
        response = client.post(
            "/estimate",
            json={"screen_count": 1, "complexity": "low"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["estimated_amount"] == 105_600
        assert data["breakdown"]["difficulty"] == 0.8

    def test_estimate_high_complexity(self, client):
        """境界ケース: 1画面, high"""
        response = client.post(
            "/estimate",
            json={"screen_count": 1, "complexity": "high"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["estimated_amount"] == 171_600
        assert data["breakdown"]["difficulty"] == 1.3

    def test_estimate_invalid_screen_count_zero(self, client):
        """不正入力: screen_count = 0"""
        response = client.post(
            "/estimate",
            json={"screen_count": 0, "complexity": "medium"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["estimated_amount"] == 0
        assert "must be > 0" in data["message"]

    def test_estimate_invalid_screen_count_negative(self, client):
        """不正入力: screen_count < 0"""
        response = client.post(
            "/estimate",
            json={"screen_count": -5, "complexity": "medium"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_estimate_invalid_complexity(self, client):
        """不正入力: unknown complexity"""
        response = client.post(
            "/estimate",
            json={"screen_count": 10, "complexity": "unknown"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["estimated_amount"] == 0
        assert "complexity must be one of" in data["message"]

    def test_estimate_invalid_screen_count_string(self, client):
        """不正入力: screen_countが文字列"""
        response = client.post(
            "/estimate",
            json={"screen_count": "abc", "complexity": "medium"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "must be an integer" in data["message"]

    def test_estimate_default_complexity(self, client):
        """complexityを省略した場合はmediumがデフォルト"""
        response = client.post(
            "/estimate",
            json={"screen_count": 10}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        # 10 × 120000 × 1.0 × 1.1 = 1,320,000
        assert data["estimated_amount"] == 1_320_000
        assert data["breakdown"]["difficulty"] == 1.0

    def test_cors_headers(self, client):
        """CORS ヘッダーが正しく設定されている"""
        response = client.post(
            "/estimate",
            json={"screen_count": 5, "complexity": "medium"}
        )
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert response.headers["Access-Control-Allow-Headers"] == "Content-Type"


# v1.2: config_version, warnings, assumptions のテスト
class TestEstimateAPIV12:
    """見積API v1.2の新機能テスト"""

    @pytest.fixture
    def client(self):
        """Flaskテストクライアント"""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_config_version_present(self, client):
        """config_versionフィールドが返る"""
        response = client.post(
            "/estimate",
            json={"screen_count": 10, "complexity": "medium"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "config_version" in data
        assert data["config_version"] == "2025-03"

    def test_warnings_empty_for_small_screen_count(self, client):
        """画面数が少ない場合、warningsは空リスト"""
        response = client.post(
            "/estimate",
            json={"screen_count": 10, "complexity": "medium"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "warnings" in data
        assert isinstance(data["warnings"], list)
        assert len(data["warnings"]) == 0

    def test_warnings_present_for_large_screen_count(self, client):
        """画面数が50以上の場合、warningsに警告が含まれる"""
        response = client.post(
            "/estimate",
            json={"screen_count": 50, "complexity": "medium"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "warnings" in data
        assert isinstance(data["warnings"], list)
        assert len(data["warnings"]) > 0
        assert "再見積を推奨" in data["warnings"][0]

    def test_assumptions_always_present(self, client):
        """assumptionsフィールドが常に返る"""
        response = client.post(
            "/estimate",
            json={"screen_count": 5, "complexity": "low"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "assumptions" in data
        assert isinstance(data["assumptions"], list)
        assert len(data["assumptions"]) == 3
        assert "要件は確定している前提です" in data["assumptions"]
        assert "デザインは既存ガイドラインを流用します" in data["assumptions"]
        assert "大規模な非機能要件は含みません" in data["assumptions"]

    def test_backward_compatibility(self, client):
        """v1.1の既存フィールドがすべて維持されている"""
        response = client.post(
            "/estimate",
            json={"screen_count": 12, "complexity": "medium"}
        )
        assert response.status_code == 200
        data = response.get_json()
        # v1.0 フィールド
        assert "status" in data
        assert "estimated_amount" in data
        assert "currency" in data
        assert "message" in data
        # v1.1 フィールド
        assert "breakdown" in data
        # v1.2 フィールド
        assert "config_version" in data
        assert "warnings" in data
        assert "assumptions" in data

