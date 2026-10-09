"""
Elifba Ses Değerlendirme & Geri Bildirim Motoru (Prototype)
Bu modül:
1. Gelen ses dosyasındaki sessizlikleri kırpar (VAD mantığı).
2. Hedef harfin fonem akustik özellikleriyle kıyaslar.
3. Türkçe konuşan çocuklara özel yönlendirici geri bildirimler üretir.
"""

import json
from pathlib import Path
from typing import Dict, Any

class ElifbaAudioEvaluator:
    def __init__(self, curriculum_path: str):
        self.curriculum_path = Path(curriculum_path)
        with open(self.curriculum_path, "r", encoding="utf-8") as f:
            self.curriculum = json.load(f)
        
        # Harf arama sözlüğü
        self.letter_map = {}
        for level in self.curriculum.get("levels", []):
            for item in level.get("items", []):
                self.letter_map[item["id"]] = item

    def evaluate_pronunciation(self, target_id: str, audio_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        target_id: Beklenen harf (örn: 'se', 'ha', 'sad')
        audio_features: Akustik modelden veya sinyal analizinden gelen veriler:
            - acoustic_score: 0-100 arası benzerlik puanı
            - detected_phoneme: modelin duyduğu en yakın fonem (örn: 'sin')
            - duration_ms: sesin uzunluğu (özellikle med harfleri için)
        """
        target_info = self.letter_map.get(target_id)
        if not target_info:
            return {"status": "error", "message": f"Bilinmeyen harf: {target_id}"}

        score = audio_features.get("acoustic_score", 0)
        detected_phoneme = audio_features.get("detected_phoneme", "")

        # Eşik değerler (Çocuklar için motivasyonel eşik: 65)
        PASSING_THRESHOLD = 65

        if score >= PASSING_THRESHOLD:
            return {
                "success": True,
                "score": score,
                "target_symbol": target_info["symbol"],
                "target_name": target_info["name"],
                "stars": 3 if score >= 85 else (2 if score >= 75 else 1),
                "feedback_title": "Harikasın! 🌟",
                "feedback_message": f"'{target_info['name']}' sesini çok güzel ve temiz çıkardın!",
                "award_xp": 10
            }
        else:
            # Hata tespiti ve Türkçe konuşan çocuğa özel ipucu
            common_errors = target_info.get("common_errors", {})
            custom_correction = common_errors.get("correction_message")
            
            # Özel yönlendirme varsa onu kullan, yoksa genel ipucunu ver
            hint = custom_correction if custom_correction else target_info.get("child_hint", "Tekrar dene!")

            return {
                "success": False,
                "score": score,
                "target_symbol": target_info["symbol"],
                "target_name": target_info["name"],
                "stars": 0,
                "feedback_title": "Çok yaklaştın! 💪",
                "feedback_message": hint,
                "award_xp": 2  # Deneme cesareti için küçük teselli puanı
            }

if __name__ == "__main__":
    import sys
    base_dir = Path(__file__).parent.parent
    curriculum_file = base_dir / "data" / "curriculum.json"
    
    evaluator = ElifbaAudioEvaluator(str(curriculum_file))
    
    print("--- Test 1: Doğru Peltek Se Okunuşu ---")
    result_success = evaluator.evaluate_pronunciation("se", {"acoustic_score": 88, "detected_phoneme": "se"})
    print(json.dumps(result_success, indent=2, ensure_ascii=False))

    print("\n--- Test 2: Hatalı Okunuş (Peltek Se yerine Sin dendiğinde) ---")
    result_fail = evaluator.evaluate_pronunciation("se", {"acoustic_score": 52, "detected_phoneme": "sin"})
    print(json.dumps(result_fail, indent=2, ensure_ascii=False))
