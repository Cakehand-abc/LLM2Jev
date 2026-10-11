import unittest

from llm2jev import Choice, JevRequest, Noul, Score


class JevRequestTests(unittest.TestCase):
    def test_serializes_complete_request(self) -> None:
        request = JevRequest(
            state={"message": "My card was charged twice.", "order_id": "A-104"},
            model="jev-latest",
            questions={
                "department": Choice(
                    instructions="Which team should handle this?",
                    criteria={"billing": None, "returns": None},
                ),
                "severity": Score(
                    instructions="How severe is this?",
                    criteria=["Low", "High"],
                ),
                "refund_requested": Noul(
                    instructions="Does the customer want a refund?",
                ),
            },
        )

        self.assertEqual(
            request.to_dict(),
            {
                "state": {"message": "My card was charged twice.", "order_id": "A-104"},
                "model": "jev-latest",
                "questions": {
                    "department": {
                        "type": "choice",
                        "criteria": {"billing": None, "returns": None},
                        "instructions": "Which team should handle this?",
                    },
                    "severity": {
                        "type": "score",
                        "criteria": ["Low", "High"],
                        "instructions": "How severe is this?",
                    },
                    "refund_requested": {
                        "type": "noul",
                        "instructions": "Does the customer want a refund?",
                    },
                },
            },
        )

    def test_accepts_string_and_array_state(self) -> None:
        question = Noul(instructions="Is this true?")

        string_request = JevRequest(
            state="A message",
            model="jev-latest",
            questions={"check": question},
        )
        array_request = JevRequest(
            state=["First message", {"message": "Second message"}],
            model="jev-latest",
            questions={"check": question},
        )

        self.assertEqual(string_request.to_dict()["state"], "A message")
        self.assertEqual(
            array_request.to_dict()["state"],
            ["First message", {"message": "Second message"}],
        )

    def test_serializes_choice_candidates_switch(self) -> None:
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                request = JevRequest(
                    state="message", model="jev-latest", questions={"check": Noul()},
                    include_choice_candidates=enabled,
                )
                self.assertEqual(request.include_choice_candidates, enabled)
                self.assertEqual(request.to_dict().get("include_choice_candidates", True), enabled)

    def test_rejects_non_boolean_choice_candidates_switch(self) -> None:
        for value in (None, 0, 1, "false", [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "include_choice_candidates"):
                JevRequest(
                    state="message", model="jev-latest", questions={"check": Noul()},
                    include_choice_candidates=value,  # type: ignore[arg-type]
                )

    def test_rejects_invalid_state(self) -> None:
        with self.assertRaises(ValueError):
            JevRequest(
                state=42,  # type: ignore[arg-type]
                model="jev-latest",
                questions={"check": Noul()},
            )

    def test_rejects_empty_model(self) -> None:
        with self.assertRaises(ValueError):
            JevRequest(state="message", model=" ", questions={"check": Noul()})

    def test_rejects_empty_questions(self) -> None:
        with self.assertRaises(ValueError):
            JevRequest(state="message", model="jev-latest", questions={})

    def test_rejects_invalid_question_id(self) -> None:
        with self.assertRaises(ValueError):
            JevRequest(state="message", model="jev-latest", questions={"": Noul()})

    def test_rejects_non_question_values(self) -> None:
        with self.assertRaises(ValueError):
            JevRequest(
                state="message",
                model="jev-latest",
                questions={"check": {"type": "noul"}},  # type: ignore[dict-item]
            )


if __name__ == "__main__":
    unittest.main()
