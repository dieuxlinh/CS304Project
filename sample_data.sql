-- This is sample data that can be inserted into the database tables.

/* INSERT INTO users (username, email, password_hash, profile_pic) VALUES ("Sophie", "sophie@gmail.com", "123", "456");
INSERT INTO users (username, email, password_hash, profile_pic) VALUES ("Linh", "Linh@gmail.com", "321", "465");
INSERT INTO users (username, email, password_hash, profile_pic) VALUES ("Ariel", "Ariel@gmail.com", "132", "654");
INSERT INTO users (username, email, password_hash, profile_pic) VALUES ("FakeUser", "fake@gmail.com", 111, 111);
INSERT INTO media (title, media_type, artist) VALUES ("Stormy Weather", 'Song', "Etta James");
INSERT INTO media (title, media_type, director) VALUES ("The Nightmare Before Christmas", 'Movie', "Henry Selick");
INSERT INTO media (title, media_type, author) VALUES ("Don Quixote", 'Book', "Miguel de Cervantes");
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (1, 1, "Good Song", 10);
INSERT INTO currents (user_id, media_id, progress) VALUES (1, 2, 50);
INSERT INTO currents (user_id, media_id, progress) VALUES (2, 3, 50)
INSERT INTO friends (user_id, friend_id) VALUES (1,2);
INSERT INTO friends (user_id, friend_id) VALUES (2,3);
INSERT INTO friends (user_id, friend_id) VALUES (1,3); */

--Should users be able to review the same media twice?
/* INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (1, 6, "I like this song", 9);
INSERT INTO currents (user_id, media_id, progress) VALUES (6, 2, 50);
INSERT INTO currents (user_id, media_id, progress) VALUES (6, 3, 50);
INSERT INTO friends (user_id, friend_id) VALUES (6,2);
INSERT INTO friends (user_id, friend_id) VALUES (6,3);
INSERT INTO friends (user_id, friend_id) VALUES (6,1); */

--Linh's additions in MEDIA
/*INSERT INTO media (title, media_type, director, artist, author) VALUES
('La La Land', 'movie', 'Damien Chazelle', NULL, NULL),
('Look What You Made Me Do', 'song', NULL, 'Taylor Swift', NULL),
('Delicate', 'song', NULL, 'Taylor Swift', NULL),
('The Midnight Sky', 'movie', 'George Clooney', NULL, NULL),
('Scandal', 'movie', 'Shonda Rhimes', NULL, NULL),
('Abbott Elementary', 'movie', 'Quinta Brunson', NULL, NULL),
('The Queen\'s Gambit', 'movie', 'Scott Frank', NULL, NULL),
('Red (Taylor\'s Version)', 'song', NULL, 'Taylor Swift', NULL),
('Pride and Prejudice', 'book', NULL, NULL, 'Jane Austen'),
('Moby-Dick', 'book', NULL, NULL, 'Herman Melville'),
('The Great Gatsby', 'book', NULL, NULL, 'F. Scott Fitzgerald'),
('1984', 'book', NULL, NULL, 'George Orwell'),
('War and Peace', 'book', NULL, NULL, 'Leo Tolstoy'),
('The Catcher in the Rye', 'book', NULL, NULL, 'J.D. Salinger'),
('Crime and Punishment', 'book', NULL, NULL, 'Fyodor Dostoevsky'),
('Wuthering Heights', 'book', NULL, NULL, 'Emily Brontë'),
('Jane Eyre', 'book', NULL, NULL, 'Charlotte Brontë'),
('The Picture of Dorian Gray', 'book', NULL, NULL, 'Oscar Wilde'),;*/

--Linh's additions into CURRENTS
/*-- Sample data for the 'currents' table

-- User 1 (Sophie) is progressing through different media
INSERT INTO currents (user_id, media_id, progress) VALUES (1, 2, 50); -- Sophie is 50% through 'The Nightmare Before Christmas'
INSERT INTO currents (user_id, media_id, progress) VALUES (1, 10, 30); -- Sophie is 30% through 'The Great Gatsby'
INSERT INTO currents (user_id, media_id, progress) VALUES (1, 12, 70); -- Sophie is 70% through 'War and Peace'

-- User 2 (Linh) is progressing through different media
INSERT INTO currents (user_id, media_id, progress) VALUES (2, 3, 90); -- Linh is 90% through 'Don Quixote'
INSERT INTO currents (user_id, media_id, progress) VALUES (2, 4, 40); -- Linh is 40% through '1984'
INSERT INTO currents (user_id, media_id, progress) VALUES (2, 14, 20); -- Linh is 20% through 'The Catcher in the Rye'

-- User 3 (Ariel) is progressing through different media
INSERT INTO currents (user_id, media_id, progress) VALUES (3, 5, 60); -- Ariel is 60% through 'Moby-Dick'
INSERT INTO currents (user_id, media_id, progress) VALUES (3, 9, 80); -- Ariel is 80% through 'Pride and Prejudice'
INSERT INTO currents (user_id, media_id, progress) VALUES (3, 13, 50); -- Ariel is 50% through 'The Queen's Gambit'
*/

--Linh's additions into REVIEWS
/*-- User 1 (Sophie) reviews various media
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (2, 1, "An iconic movie that never gets old!", 10); -- Review for 'The Nightmare Before Christmas' (Movie)
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (10, 1, "A captivating story, though quite long.", 8); -- Review for 'The Great Gatsby' (Book)
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (12, 1, "Don't love, though tough to finish.", 5); -- Review for 'War and Peace' (Book)

-- User 2 (Linh) reviews various media
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (3, 2, "Read for class, it was okay.", 6); -- Review for 'Don Quixote' (Book)
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (4, 2, "Very relevant.", 9); -- Review for '1984' (Book)
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (14, 2, "The Catcher in the Rye captures emotions very well.", 8); -- Review for 'The Catcher in the Rye' (Book)

-- User 3 (Ariel) reviews various media
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (5, 3, "Moby-Dick is such a childhood classic, I like it a lot.", 7); -- Review for 'Moby-Dick' (Book)
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (9, 3, "Pride and Prejudice is a timeless romance, beautifully written.", 10); -- Review for 'Pride and Prejudice' (Book)
INSERT INTO reviews (media_id, user_id, review_text, rating) VALUES (13, 3, "The Queen's Gambit is fantastic and very engaging.", 9); -- Review for 'The Queen's Gambit' (TV Show)
*/