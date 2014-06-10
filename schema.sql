CREATE TABLE IF NOT EXISTS `f1_bot` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `subreddit` text COLLATE utf8_swedish_ci NOT NULL,
  `title` text COLLATE utf8_swedish_ci NOT NULL,
  `text` text COLLATE utf8_swedish_ci NOT NULL,
  `flair_text` varchar(255) COLLATE utf8_swedish_ci NOT NULL DEFAULT '',
  `flair_css` varchar(255) COLLATE utf8_swedish_ci NOT NULL DEFAULT '',
  `schedule` datetime NOT NULL,
  `posted` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COLLATE=utf8_swedish_ci;
