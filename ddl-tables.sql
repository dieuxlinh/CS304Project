use recap_db;

drop table if exists friends;
drop table if exists currents;
drop table if exists reviews;
drop table if exists users;
drop table if exists media;

create table users (
    user_id int auto_increment,
    username varchar(20),
    email varchar(50),
    password_hash varchar(255),
    profile_pic varchar(255),
    primary key (user_id)
);

create table friends (
    user_id int not null,
    friend_id int not null,
    primary key (user_id, friend_id),

    
    index(user_id),
    foreign key (user_id) references users(user_id)
        on update restrict
        on delete cascade
);

create table media(
    media_id int auto_increment,
    title varchar(50),
    media_type enum('movie', 'song', 'book'),
    `release` int,
    director varchar(50),
    artist varchar(50),
    author varchar(50),
    primary key(media_id)
);

create table currents(
    current_id int auto_increment,
    user_id int not null,
    media_id int,
    progress varchar(50),
    primary key(current_id),

    index(user_id, media_id),
    foreign key (user_id) references users(user_id)
        on update restrict
        on delete cascade,
     foreign key (media_id) references media(media_id)
        on update restrict
        on delete cascade
);

create table reviews(
    review_id int auto_increment,
    media_id int,
    user_id int,
    review_text text,
    rating int,
    primary key(review_id),

    foreign key (user_id) references users(user_id)
        on update restrict
        on delete cascade,
     foreign key (media_id) references media(media_id)
        on update restrict
        on delete cascade
);
