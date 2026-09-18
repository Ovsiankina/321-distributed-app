export interface Video {
  id: string
  title: string
  thumbnail: string
  duration: string
  tags: string[]
}

export const videos: Video[] = [
  {
    id: '1',
    title: 'Apprendre TypeScript en 45 minutes',
    thumbnail: 'https://picsum.photos/seed/video-1/480/270',
    duration: '45:12',
    tags: ['tech', 'programmation'],
  },
  {
    id: '2',
    title: 'Session live de musique acoustique',
    thumbnail: 'https://picsum.photos/seed/video-2/480/270',
    duration: '32:04',
    tags: ['musique'],
  },
  {
    id: '3',
    title: 'Speedrun complet : niveau expert',
    thumbnail: 'https://picsum.photos/seed/video-3/480/270',
    duration: '28:47',
    tags: ['gaming'],
  },
  {
    id: '4',
    title: 'Recette : risotto aux champignons',
    thumbnail: 'https://picsum.photos/seed/video-4/480/270',
    duration: '22:15',
    tags: ['cuisine'],
  },
  {
    id: '5',
    title: 'Les bases de l’architecture distribuée',
    thumbnail: 'https://picsum.photos/seed/video-5/480/270',
    duration: '38:53',
    tags: ['tech', 'science'],
  },
  {
    id: '6',
    title: 'Match amical : les temps forts',
    thumbnail: 'https://picsum.photos/seed/video-6/480/270',
    duration: '41:30',
    tags: ['sport'],
  },
  {
    id: '7',
    title: 'Comprendre la relativité restreinte',
    thumbnail: 'https://picsum.photos/seed/video-7/480/270',
    duration: '35:20',
    tags: ['science'],
  },
  {
    id: '8',
    title: 'Concert intimiste : reprises de jazz',
    thumbnail: 'https://picsum.photos/seed/video-8/480/270',
    duration: '29:41',
    tags: ['musique'],
  },
  {
    id: '9',
    title: 'Découverte d’un jeu indé en coopératif',
    thumbnail: 'https://picsum.photos/seed/video-9/480/270',
    duration: '44:02',
    tags: ['gaming', 'tech'],
  },
]
