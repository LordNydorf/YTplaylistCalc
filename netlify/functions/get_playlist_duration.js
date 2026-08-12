/**
 * Netlify Serverless Function: get_playlist_duration
 * Native Node.js handler for ultra-fast, zero-dependency Netlify deployment.
 */

function extractPlaylistId(urlOrId) {
  if (!urlOrId) return null;
  const str = String(urlOrId).trim();
  const match = str.match(/[?&]list=([a-zA-Z0-9_-]+)/);
  if (match) return match[1];
  if (/^[a-zA-Z0-9_-]{10,}$/.test(str)) return str;
  return null;
}

function parseISODuration(duration) {
  if (!duration) return 0;
  const match = duration.match(/P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return 0;
  const days = parseInt(match[1] || 0, 10);
  const hours = parseInt(match[2] || 0, 10);
  const minutes = parseInt(match[3] || 0, 10);
  const seconds = parseInt(match[4] || 0, 10);
  return days * 86400 + hours * 3600 + minutes * 60 + seconds;
}

function formatDuration(totalSeconds) {
  const s = Math.max(0, Math.round(totalSeconds));
  const days = Math.floor(s / 86400);
  const rem1 = s % 86400;
  const hours = Math.floor(rem1 / 3600);
  const rem2 = rem1 % 3600;
  const minutes = Math.floor(rem2 / 60);
  const seconds = rem2 % 60;

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0 || days > 0) parts.push(`${hours}h`);
  if (minutes > 0 || hours > 0 || days > 0) parts.push(`${minutes}m`);
  parts.push(`${seconds}s`);

  const verboseParts = [];
  if (days > 0) verboseParts.push(`${days} ${days === 1 ? 'day' : 'days'}`);
  if (hours > 0) verboseParts.push(`${hours} ${hours === 1 ? 'hour' : 'hours'}`);
  if (minutes > 0) verboseParts.push(`${minutes} ${minutes === 1 ? 'minute' : 'minutes'}`);
  if (seconds > 0 || verboseParts.length === 0) verboseParts.push(`${seconds} seconds`);

  return {
    text: parts.join(' '),
    verbose: verboseParts.join(', '),
    days,
    hours,
    minutes,
    seconds,
    totalSeconds: s
  };
}

function formatTimeSaved(originalSeconds, speedSeconds) {
  const saved = Math.max(0, Math.round(originalSeconds - speedSeconds));
  if (saved === 0) return '0m';
  const hours = Math.floor(saved / 3600);
  const mins = Math.floor((saved % 3600) / 60);
  if (hours > 0) return `${hours}h ${mins}m saved`;
  return `${mins}m saved`;
}

exports.handler = async function(event, context) {
  const headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS, GET'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers, body: '' };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method Not Allowed. Please use POST.' })
    };
  }

  let bodyData = {};
  try {
    bodyData = typeof event.body === 'string' ? JSON.parse(event.body || '{}') : (event.body || {});
  } catch (err) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Invalid JSON payload in request body.' })
    };
  }

  const playlistUrl = (bodyData.url || '').trim();
  if (!playlistUrl) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Please provide a YouTube playlist URL or ID.' })
    };
  }

  const playlistId = extractPlaylistId(playlistUrl);
  if (!playlistId) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'Invalid YouTube playlist URL or ID.' })
    };
  }

  const apiKey = process.env.YOUTUBE_API_KEY;
  if (!apiKey) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'YOUTUBE_API_KEY is not configured in Netlify environment variables.' })
    };
  }

  try {
    // 1. Fetch Playlist Metadata
    const pMetaUrl = `https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&id=${playlistId}&key=${apiKey}`;
    const pMetaRes = await fetch(pMetaUrl);
    const pMetaData = await pMetaRes.json();

    if (pMetaData.error) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: pMetaData.error.message || 'Error fetching playlist metadata.' })
      };
    }

    if (!pMetaData.items || pMetaData.items.length === 0) {
      return {
        statusCode: 404,
        headers,
        body: JSON.stringify({ error: 'Playlist not found. Make sure it is public or unlisted.' })
      };
    }

    const playlistItem = pMetaData.items[0];
    const snippet = playlistItem.snippet || {};
    const thumbs = snippet.thumbnails || {};
    const thumbUrl = (thumbs.maxres && thumbs.maxres.url) ||
                     (thumbs.high && thumbs.high.url) ||
                     (thumbs.medium && thumbs.medium.url) ||
                     (thumbs.default && thumbs.default.url) || '';

    const playlistInfo = {
      id: playlistId,
      title: snippet.title || 'YouTube Playlist',
      channelTitle: snippet.channelTitle || 'Unknown Creator',
      channelId: snippet.channelId || '',
      description: snippet.description || '',
      publishedAt: snippet.publishedAt || '',
      thumbnail: thumbUrl,
      itemCount: (playlistItem.contentDetails && playlistItem.contentDetails.itemCount) || 0
    };

    // 2. Fetch Playlist Items with Pagination
    const videoEntries = [];
    let nextPageToken = null;
    let page = 0;
    const maxPages = 10; // Up to 500 videos

    while (page < maxPages) {
      page++;
      let itemsUrl = `https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId=${playlistId}&maxResults=50&key=${apiKey}`;
      if (nextPageToken) {
        itemsUrl += `&pageToken=${nextPageToken}`;
      }

      const itemsRes = await fetch(itemsUrl);
      const itemsData = await itemsRes.json();

      if (itemsData.error) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: itemsData.error.message || 'Error fetching playlist items.' })
        };
      }

      const items = itemsData.items || [];
      if (items.length === 0 && page === 1) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'This playlist is empty or contains no accessible videos.' })
        };
      }

      for (const item of items) {
        const cDetails = item.contentDetails || {};
        const vId = cDetails.videoId;
        const vSnippet = item.snippet || {};
        const vTitle = vSnippet.title || 'Unavailable video';

        if (vTitle === 'Private video' || vTitle === 'Deleted video' || !vId) {
          continue;
        }

        const vThumbs = vSnippet.thumbnails || {};
        const vThumb = (vThumbs.medium && vThumbs.medium.url) ||
                       (vThumbs.default && vThumbs.default.url) || '';

        videoEntries.push({
          id: vId,
          title: vTitle,
          thumbnail: vThumb,
          channelTitle: vSnippet.videoOwnerChannelTitle || snippet.channelTitle || '',
          position: videoEntries.length + 1
        });
      }

      nextPageToken = itemsData.nextPageToken;
      if (!nextPageToken) break;
    }

    if (videoEntries.length === 0) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'No accessible videos found in this playlist.' })
      };
    }

    // 3. Batch Fetch Video Durations
    const videoMap = {};
    for (let i = 0; i < videoEntries.length; i += 50) {
      const chunk = videoEntries.slice(i, i + 50);
      const chunkIds = chunk.map(v => v.id).join(',');
      const vUrl = `https://www.googleapis.com/youtube/v3/videos?part=contentDetails,snippet&id=${chunkIds}&key=${apiKey}`;

      const vRes = await fetch(vUrl);
      const vData = await vRes.json();

      if (vData.items) {
        for (const vItem of vData.items) {
          const vid = vItem.id;
          const durIso = (vItem.contentDetails && vItem.contentDetails.duration) || 'PT0S';
          const durSecs = parseISODuration(durIso);
          videoMap[vid] = {
            durationSeconds: durSecs,
            durationFormatted: formatDuration(durSecs).text
          };
        }
      }
    }

    const validVideos = [];
    let totalSeconds = 0;
    let shortestVideo = null;
    let longestVideo = null;

    for (const v of videoEntries) {
      const details = videoMap[v.id];
      if (!details) continue;
      v.durationSeconds = details.durationSeconds;
      v.duration = details.durationFormatted;
      validVideos.push(v);
      totalSeconds += v.durationSeconds;

      if (v.durationSeconds > 0) {
        if (!shortestVideo || v.durationSeconds < shortestVideo.durationSeconds) {
          shortestVideo = v;
        }
        if (!longestVideo || v.durationSeconds > longestVideo.durationSeconds) {
          longestVideo = v;
        }
      }
    }

    if (validVideos.length === 0) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Could not extract duration data for videos in this playlist.' })
      };
    }

    playlistInfo.videoCount = validVideos.length;
    if (!playlistInfo.thumbnail && validVideos[0]) {
      playlistInfo.thumbnail = validVideos[0].thumbnail;
    }

    const speedFactors = [1.0, 1.25, 1.5, 1.75, 2.0];
    const speeds = {};
    for (const sf of speedFactors) {
      const adjSecs = Math.round(totalSeconds / sf);
      speeds[String(sf)] = {
        speed: sf,
        seconds: adjSecs,
        formatted: formatDuration(adjSecs),
        timeSaved: formatTimeSaved(totalSeconds, adjSecs)
      };
    }

    const avgSecs = validVideos.length > 0 ? Math.round(totalSeconds / validVideos.length) : 0;
    const formattedTotal = formatDuration(totalSeconds);

    const result = {
      playlist: playlistInfo,
      totalSeconds,
      formatted: formattedTotal,
      totalDuration: formattedTotal.verbose,
      speeds,
      stats: {
        avgSeconds: avgSecs,
        avgFormatted: formatDuration(avgSecs).text,
        shortest: shortestVideo ? {
          title: shortestVideo.title,
          duration: shortestVideo.duration,
          seconds: shortestVideo.durationSeconds
        } : null,
        longest: longestVideo ? {
          title: longestVideo.title,
          duration: longestVideo.duration,
          seconds: longestVideo.durationSeconds
        } : null
      },
      videos: validVideos
    };

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(result)
    };

  } catch (err) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Server error processing playlist: ' + err.message })
    };
  }
};
