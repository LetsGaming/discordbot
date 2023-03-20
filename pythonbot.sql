-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Erstellungszeit: 02. Mrz 2023 um 01:31
-- Server-Version: 10.4.27-MariaDB
-- PHP-Version: 8.1.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `pythonbot`
--

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `birthdays`
--

CREATE TABLE birthdays (
  id INT NOT NULL AUTO_INCREMENT,
  guild_id BIGINT NOT NULL,
  discord_id VARCHAR(255) NOT NULL,
  date DATE NOT NULL
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Tabellenstruktur für Tabelle `members`
--

CREATE TABLE `members` (
  `id` int(11) NOT NULL,
  `guild_id` bigint(25) NOT NULL,
  `discord_id` varchar(50) NOT NULL,
  `team_id` int(11) NOT NULL,
  `leader` tinyint(4) NOT NULL,
  `project_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Daten für Tabelle `members`
--

INSERT INTO `members` (`id`, `guild_id`, `discord_id`, `team_id`, `project_id`) VALUES
(1, 1075667809100628028, '<@468675411144867842>', 1, 1),
(2, 1075667809100628028, '<@691398978851438652>', 1, 1),
(3, 1075667809100628028, '<@677248867422699541>', 1, 1),
(4, 1075667809100628028, '<@272402865874534400>', 2, 1),
(5, 1075667809100628028, '<@581134027390451733>', 2, 1),
(6, 1075667809100628028, '<@890500578311032862>', 2, 1),
(7, 1075667809100628028, '<@256857193532358666>', 2, 1),
(8, 1075667809100628028, '<@483662581706391562>', 3, 1),
(9, 1075667809100628028, '<@1070421464991404145>', 3, 1),
(10, 1075667809100628028, '<@767079312720396308>', 3, 1),
(11, 1075667809100628028, '<@788739422493474827>', 3, 1),
(12, 1075667809100628028, '<@468675411144867842>', 4, 2),
(13, 1075667809100628028, '<@767079312720396308>', 4, 2),
(14, 1075667809100628028, '<@788739422493474827>', 4, 2),
(15, 1075667809100628028, '<@1070421464991404145>', 5, 2),
(16, 1075667809100628028, '<@890500578311032862>', 5, 2),
(17, 1075667809100628028, '<@691398978851438652>', 5, 2),
(18, 1075667809100628028, '<@677248867422699541>', 5, 2),
(19, 1075667809100628028, '<@272402865874534400>', 6, 2),
(20, 1075667809100628028, '<@483662581706391562>', 6, 2),
(21, 1075667809100628028, '<@256857193532358666>', 6, 2),
(22, 1075667809100628028, '<@581134027390451733>', 7, 2);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `projects`
--

CREATE TABLE `projects` (
  `id` int(50) NOT NULL,
  `guild_id` bigint(25) NOT NULL,
  `name` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Daten für Tabelle `projects`
--

INSERT INTO `projects` (`id`, `guild_id`, `name`) VALUES
(1, 1075667809100628028, 'BevBot'),
(2, 1075667809100628028, 'EscapeRoom');

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `quote`
--

CREATE TABLE `quote` (
  `quote_id` int(11) NOT NULL,
  `guild_id` bigint(25) NOT NULL,
  `quote_date` date NOT NULL,
  `username` varchar(50) NOT NULL,
  `user_avatar` varchar(255) NOT NULL,
  `quote_text` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Daten für Tabelle `quote`
--

INSERT INTO `quote` (`quote_id`, `guild_id`, `quote_date`, `username`, `user_avatar`, `quote_text`) VALUES
(2, 1043909951191535656, '2023-01-31', '『米蘭』', 'https://cdn.discordapp.com/avatars/332527004606005248/abe0059e5826e7a4fb0380bef04354dc.png?size=1024', 'i don\'t have a job i already work as a discord mod'),
(3, 1043909951191535656, '2023-02-01', 'LetsGamingDE', 'https://cdn.discordapp.com/avatars/272402865874534400/4de66dd5df030ce9f31008675a6ee6c0.png?size=1024', 'Kämpft gegen Malphite: Warum macht dieser Stein denn so viel Damage? So hab ich Kleinstein nicht in Erinnerung ;-;'),
(4, 1043909951191535656, '2023-02-01', '『米蘭』', 'https://cdn.discordapp.com/avatars/332527004606005248/abe0059e5826e7a4fb0380bef04354dc.png?size=1024', 'Ich wie ich in Mathe einfach nichts verstehe: https://cdn.discordapp.com/attachments/1026274535936376923/1070334973619486851/image.png'),
(5, 1043909951191535656, '2023-02-01', 'LetsGamingDE', 'https://cdn.discordapp.com/avatars/272402865874534400/4de66dd5df030ce9f31008675a6ee6c0.png?size=1024', 'Domenic : Das ist ein Semilocon. / Mill : ...Meinst du Semicolon? / Domenic : Ja Semilocolon.'),
(6, 1043909951191535656, '2023-02-01', 'zeid', 'https://cdn.discordapp.com/avatars/434803179323129870/a26f4b49f8723279c326a46c69c54430.png?size=1024', 'Joined voice-channel: Mil: OMG, es ist ein wildes Micah. Micah: Okay, haltet jetzt alle wieder eure Fressen');

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `teams`
--

CREATE TABLE `teams` (
  `id` int(11) NOT NULL,
  `guild_id` bigint(25) NOT NULL,
  `name` varchar(50) NOT NULL,
  `description` varchar(255) NOT NULL,
  `project_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Daten für Tabelle `teams`
--

INSERT INTO `teams` (`id`, `guild_id`, `name`, `description`, `project_id`) VALUES
(1, 1075667809100628028, 'Managment', '', 1),
(2, 1075667809100628028, 'Software', '', 1),
(3, 1075667809100628028, 'Hardware', '', 1),
(4, 1075667809100628028, 'Managment', '', 2),
(5, 1075667809100628028, 'Webdesign', '', 2),
(6, 1075667809100628028, 'Entwicklung', '', 2),
(7, 1075667809100628028, 'Spielplan', '', 2);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `tickets`
--

CREATE TABLE `tickets` (
  `id` int(11) NOT NULL,
  `guild_id` bigint(25) NOT NULL,
  `project_id` int(11) NOT NULL,
  `team_id` int(11) NOT NULL,
  `member_id` int(11) NOT NULL,
  `ticket_author` varchar(50),
  `ticket_author_icon` varchar(255),
  `ticket_title` varchar(50) NOT NULL,
  `ticket_description` varchar(255) NOT NULL,
  `deadline` date NOT NULL,
  `resolved` tinyint(4) NOT NULL,
  `resolve_date` date DEFAULT NULL,
  `creation_date` date,
  `assigned_team_id` int(11) DEFAULT NULL,
  `assigned_member_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Daten für Tabelle `tickets`
--

INSERT INTO `tickets` (`id`, `guild_id`, `project_id`, `team_id`, `member_id`, `ticket_title`, `ticket_description`, `deadline`, `resolved`, `resolve_date`) VALUES
(1, 1075667809100628028, 1, 2, 4, 'BeispielTicket', 'Dies ist nur ein Beispiel', '2023-02-28', 1, '2023-02-28');

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `birthdays`
--
ALTER TABLE `members`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `members`
--
ALTER TABLE `members`
  ADD PRIMARY KEY (`id`),
  ADD KEY `team_id` (`team_id`),
  ADD KEY `project_id` (`project_id`);

--
-- Indizes für die Tabelle `projects`
--
ALTER TABLE `projects`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `quote`
--
ALTER TABLE `quote`
  ADD PRIMARY KEY (`quote_id`);

--
-- Indizes für die Tabelle `teams`
--
ALTER TABLE `teams`
  ADD PRIMARY KEY (`id`),
  ADD KEY `project_id` (`project_id`);

--
-- Indizes für die Tabelle `tickets`
--
ALTER TABLE `tickets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `project_id` (`project_id`),
  ADD KEY `team_id` (`team_id`),
  ADD KEY `member_id` (`member_id`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `members`
--
ALTER TABLE `members`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT für Tabelle `projects`
--
ALTER TABLE `projects`
  MODIFY `id` int(50) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT für Tabelle `quote`
--
ALTER TABLE `quote`
  MODIFY `quote_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT für Tabelle `teams`
--
ALTER TABLE `teams`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT für Tabelle `tickets`
--
ALTER TABLE `tickets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
