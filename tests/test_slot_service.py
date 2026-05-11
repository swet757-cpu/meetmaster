from datetime import date, datetime
import unittest

from app.services.slot_service import (
    BookingSettings,
    TimeInterval,
    available_booking_dates,
    generate_slots,
)


class SlotServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = BookingSettings()

    def test_weekend_has_no_slots(self) -> None:
        slots = generate_slots(
            target_date=date(2026, 5, 16),
            duration_minutes=30,
            now=datetime(2026, 5, 11, 9, 0),
            settings=self.settings,
        )

        self.assertEqual(slots, [])

    def test_closed_day_has_no_slots(self) -> None:
        target = date(2026, 5, 13)

        slots = generate_slots(
            target_date=target,
            duration_minutes=30,
            now=datetime(2026, 5, 11, 9, 0),
            closed_dates={target},
            settings=self.settings,
        )

        self.assertEqual(slots, [])

    def test_slots_are_inside_workday(self) -> None:
        slots = generate_slots(
            target_date=date(2026, 5, 13),
            duration_minutes=60,
            now=datetime(2026, 5, 11, 9, 0),
            settings=self.settings,
        )

        self.assertTrue(slots)
        self.assertEqual(slots[0].start.time().strftime("%H:%M"), "09:00")
        self.assertEqual(slots[-1].start.time().strftime("%H:%M"), "16:00")
        self.assertEqual(slots[-1].end.time().strftime("%H:%M"), "17:00")

    def test_min_notice_day_is_applied(self) -> None:
        slots = generate_slots(
            target_date=date(2026, 5, 12),
            duration_minutes=30,
            now=datetime(2026, 5, 11, 16, 30),
            settings=self.settings,
        )

        self.assertEqual(slots[0].start, datetime(2026, 5, 12, 16, 30))

    def test_busy_interval_and_buffer_are_applied(self) -> None:
        slots = generate_slots(
            target_date=date(2026, 5, 13),
            duration_minutes=30,
            now=datetime(2026, 5, 11, 9, 0),
            busy_intervals=[
                TimeInterval(
                    start=datetime(2026, 5, 13, 10, 0),
                    end=datetime(2026, 5, 13, 10, 30),
                )
            ],
            settings=self.settings,
        )
        starts = {slot.start.time().strftime("%H:%M") for slot in slots}

        self.assertIn("09:15", starts)
        self.assertNotIn("09:30", starts)
        self.assertNotIn("09:45", starts)
        self.assertNotIn("10:00", starts)
        self.assertNotIn("10:15", starts)
        self.assertNotIn("10:30", starts)
        self.assertIn("10:45", starts)

    def test_available_booking_dates_exclude_weekends_and_closed_days(self) -> None:
        dates = available_booking_dates(
            now=datetime(2026, 5, 11, 9, 0),
            closed_dates={date(2026, 5, 13)},
            settings=self.settings,
            days_ahead=7,
        )

        self.assertNotIn(date(2026, 5, 13), dates)
        self.assertNotIn(date(2026, 5, 16), dates)
        self.assertNotIn(date(2026, 5, 17), dates)
        self.assertIn(date(2026, 5, 12), dates)


if __name__ == "__main__":
    unittest.main()
