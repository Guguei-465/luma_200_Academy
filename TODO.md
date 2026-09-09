# TODO: Add recipient field to Announcement

- [x] 1. Add `recipient` FK field to `Announcement` model in `anouncements/models.py`
- [x] 2. Add `recipient` to `AnnouncementSerializer` fields in `anouncements/serializers.py`
- [x] 3. Update `perform_create` in `anouncements/views.py` to notify only the recipient if set, otherwise broadcast
- [x] 4. Update `resend` action in `anouncements/views.py` to respect `recipient`
- [x] 5. Generate migration for the new field
