# Paw World — API Endpoint Reference

Organized by service. Duplicates removed, missing CRUD filled in, and a Rescue Network service added.

---

## 1. Auth Service
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh-token
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
GET    /api/auth/me
```

---

## 2. User Service
*(Follow System merged in here — no more duplicate follower/following routes)*
```
GET    /api/users
GET    /api/users/{user_id}
PUT    /api/users/{user_id}
DELETE /api/users/{user_id}
GET    /api/users/{user_id}/followers
GET    /api/users/{user_id}/following
GET    /api/users/{user_id}/cats
POST   /api/users/{user_id}/follow
DELETE /api/users/{user_id}/follow
POST   /api/users/{user_id}/block
DELETE /api/users/{user_id}/block
GET    /api/users/blocked
```

---

## 3. Profile Service
```
GET    /api/profile
PUT    /api/profile
POST   /api/profile/avatar
POST   /api/profile/banner
```

---

## 4. Posts Service
```
POST   /api/posts
GET    /api/posts
GET    /api/posts/{post_id}
PUT    /api/posts/{post_id}
DELETE /api/posts/{post_id}
GET    /api/posts/user/{user_id}
```

---

## 5. Likes Service
```
POST   /api/posts/{post_id}/like
DELETE /api/posts/{post_id}/like
GET    /api/posts/{post_id}/likes
```

---

## 6. Comments Service
```
POST   /api/posts/{post_id}/comments
GET    /api/posts/{post_id}/comments
PUT    /api/comments/{comment_id}
DELETE /api/comments/{comment_id}
POST   /api/comments/{comment_id}/reply
```

---

## 7. Feed Service
```
GET    /api/feed
GET    /api/feed/trending
GET    /api/feed/explore
```

---

## 8. Stories Service
```
POST   /api/stories
GET    /api/stories
GET    /api/stories/{story_id}
DELETE /api/stories/{story_id}
POST   /api/stories/{story_id}/view
```

---

## 9. Search Service
*(expanded — `pet_type` and `area` are shared filters reused across hotels, products, vets, rescue listings, and breeders)*
```
GET    /api/search?q=&type=

GET    /api/search/users?q=&area=
GET    /api/search/posts?q=
GET    /api/search/hashtags?q=

GET    /api/search/hotels?q=&area=&pet_type=&check_in=&check_out=&price_min=&price_max=&rating_min=&amenities=
GET    /api/search/products?q=&category=&pet_type=&price_min=&price_max=&in_stock=
GET    /api/search/vets?q=&area=&specialty=&pet_type=
GET    /api/search/rescue-listings?q=&area=&pet_type=&breed=&age_min=&age_max=&gender=&size=
GET    /api/search/breeders?q=&area=&pet_type=&breed=

GET    /api/search/filters?type=
```
- `type=` on `/api/search` is one of `users | posts | hotels | products | vets | rescue-listings | breeders`, for a single cross-entity search bar.
- `pet_type` defaults to `cat` for now, but is named generically in case Paw World ever expands beyond cats.
- `/api/search/filters?type=hotels` returns the valid values for that resource's filters (areas in use, amenity list, price bounds, etc.) so dropdowns stay in sync with real data instead of being hardcoded on the frontend.
- These are convenience aggregator endpoints. The same `area`/`pet_type`/etc. query params also work directly on the resource's own list endpoint (see `GET /hotels`, `GET /products`, `GET /rescue/listings` below) for components that are already scoped to one resource type.

---

## 10. Hashtags Service
```
GET    /api/hashtags/{tag}
GET    /api/hashtags/{tag}/posts
```

---

## 11. Bookmarks Service
```
POST   /api/posts/{post_id}/save
DELETE /api/posts/{post_id}/save
GET    /api/saved-posts
```

---

## 12. Cat Profile Service
*(vaccinations and medical-records moved to Healthcare Service — see #14)*
```
POST   /cats
GET    /cats
GET    /cats/{cat_id}
PUT    /cats/{cat_id}
DELETE /cats/{cat_id}
GET    /cats/user/{user_id}
POST   /cats/{cat_id}/photos
DELETE /cats/{cat_id}/photos/{photo_id}
```

---

## 13. Hotel & Booking Service
*(added hotel update/delete, and a list-my-bookings endpoint)*
```
POST   /hotels
GET    /hotels?area=&pet_type=&check_in=&check_out=&price_min=&price_max=&rating_min=&amenities=
GET    /hotels/{hotel_id}
PUT    /hotels/{hotel_id}
DELETE /hotels/{hotel_id}
GET    /hotels/{hotel_id}/availability

POST   /bookings
GET    /bookings
GET    /bookings/{booking_id}
POST   /bookings/{booking_id}/cancel
PUT    /bookings/{booking_id}/status
```

---

## 14. Healthcare Service
*(vaccinations + medical/health records consolidated here, keyed by cat_id)*
```
POST   /appointments
GET    /appointments
GET    /appointments/{appointment_id}
PUT    /appointments/{appointment_id}/status

POST   /health-records
GET    /health-records/{cat_id}

POST   /vaccinations
GET    /vaccinations/{cat_id}

GET    /vets?area=&specialty=&pet_type=
GET    /vets/{vet_id}
```

---

## 15. Marketplace Service
*(added product update/delete, full cart CRUD, and order management)*
```
POST   /products
GET    /products?category=&pet_type=&price_min=&price_max=&in_stock=
GET    /products/{product_id}
PUT    /products/{product_id}
DELETE /products/{product_id}

GET    /cart
POST   /cart
PUT    /cart/{item_id}
DELETE /cart/{item_id}

POST   /orders
GET    /orders
GET    /orders/{order_id}
PUT    /orders/{order_id}/status
```

---

## 16. Cat Breeding Service
```
POST   /breeding/profiles
GET    /breeding/profiles?area=&pet_type=&breed=
GET    /breeding/profiles/{profile_id}
PUT    /breeding/profiles/{profile_id}
DELETE /breeding/profiles/{profile_id}

POST   /breeding/match-request
GET    /breeding/matches
PUT    /breeding/matches/{match_id}/status
```

---

## 17. Rescue Network Service *(new)*
```
POST   /rescue/organizations
GET    /rescue/organizations
GET    /rescue/organizations/{org_id}
PUT    /rescue/organizations/{org_id}

POST   /rescue/listings
GET    /rescue/listings?area=&pet_type=&breed=&age_min=&age_max=&gender=&size=
GET    /rescue/listings/{listing_id}
PUT    /rescue/listings/{listing_id}
DELETE /rescue/listings/{listing_id}

POST   /rescue/applications
GET    /rescue/applications
GET    /rescue/applications/{application_id}
PUT    /rescue/applications/{application_id}/status

POST   /rescue/donations
GET    /rescue/donations/{org_id}
```

---

## 18. Reviews & Ratings Service *(new)*
```
POST   /reviews
GET    /reviews?target_type=&target_id=
PUT    /reviews/{review_id}
DELETE /reviews/{review_id}
```
*`target_type` covers `hotel`, `vet`, `product`, `seller`, `breeder`, etc.*

---

## 19. Reports & Moderation Service *(new)*
```
POST   /reports
GET    /reports
PUT    /reports/{report_id}/status
```
*Used for reporting posts, comments, users, products, or listings.*

---

## 20. Messaging Service *(new — consider for v2)*
```
GET    /conversations
POST   /conversations
GET    /conversations/{conversation_id}/messages
POST   /conversations/{conversation_id}/messages
PUT    /messages/{message_id}/read
```

---

## 21. Payments Service *(new)*
```
POST   /payments/checkout
GET    /payments/{payment_id}
POST   /payments/{payment_id}/refund
GET    /payment-methods
POST   /payment-methods
DELETE /payment-methods/{method_id}
```

---

## 22. Notifications Service
*(added preference + device registration endpoints)*
```
GET    /notifications
POST   /notifications/read
GET    /notifications/preferences
PUT    /notifications/preferences
POST   /notifications/devices
DELETE /notifications/devices/{device_id}
```