import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker';
import { speakRecommendedAction, stopSpeaking } from '../audio/speak';
import { CONFIDENCE_THRESHOLD, CROPS, diseaseInfo, type CropId } from '../data/diseaseClasses';
import { marketPriceFor, priceChangePercent } from '../data/marketPrices';
import { sampleLeafPhotoUri } from '../data/samplePhotos';
import { pendingSyncCount, saveObservation } from '../db/db';
import { getCurrentCoordinates } from '../location/getLocation';
import { AVAILABLE_CROPS, classifyLeafPhoto, preloadModel, type ClassifyResult } from '../ml/model';
import { syncPendingObservations } from '../sync/syncObservations';
import { uuidv4 } from '../util/uuid';

export default function HomeScreen(): React.JSX.Element {
  const [modelReady, setModelReady] = useState(false);
  const [cropId, setCropId] = useState<CropId>(AVAILABLE_CROPS[0] ?? 'bean');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [result, setResult] = useState<ClassifyResult | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [syncing, setSyncing] = useState(false);
  const [lastSyncNote, setLastSyncNote] = useState<string | null>(null);
  const [lastCoords, setLastCoords] = useState<{ lat: number; lon: number } | null>(null);

  useEffect(() => {
    preloadModel()
      .then(() => setModelReady(true))
      .catch((err) => Alert.alert('Model failed to load', String(err)));
    refreshPendingCount();
    attemptSync(); // opportunistic: flush anything left over from a prior offline session
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount-only by design
  }, []);

  function refreshPendingCount() {
    pendingSyncCount().then(setPendingCount).catch(() => {});
  }

  async function attemptSync() {
    setSyncing(true);
    try {
      const syncResult = await syncPendingObservations();
      if (syncResult.synced > 0) {
        setLastSyncNote(`Synced ${syncResult.synced} observation${syncResult.synced === 1 ? '' : 's'} to the cooperative server.`);
      } else if (syncResult.error) {
        setLastSyncNote(null); // offline/unreachable — expected, stay quiet per ARCHITECTURE.md §3
      }
      refreshPendingCount();
    } finally {
      setSyncing(false);
    }
  }

  async function pickAndClassify() {
    const response = await launchImageLibrary({ mediaType: 'photo', quality: 0.9 });
    if (response.didCancel || !response.assets?.[0]?.uri) return;
    await classify(response.assets[0].uri);
  }

  async function classifySample() {
    await classify(sampleLeafPhotoUri(cropId));
  }

  async function classify(uri: string) {
    stopSpeaking();
    setPhotoUri(uri);
    setResult(null);
    setClassifying(true);
    try {
      // Run inference and the (best-effort, optional) GPS fix in parallel —
      // a slow/denied location fix must never hold up the diagnosis itself.
      const [prediction, coords] = await Promise.all([
        classifyLeafPhoto(uri, cropId),
        getCurrentCoordinates(),
      ]);
      setResult(prediction);
      setLastCoords(coords);

      const belowThreshold = prediction.confidence < CONFIDENCE_THRESHOLD;
      await saveObservation({
        id: uuidv4(),
        cropId,
        photoUri: uri,
        capturedAt: new Date().toISOString(),
        predictedClass: prediction.predictedClass,
        confidence: prediction.confidence,
        topClasses: prediction.classProbabilities,
        belowThreshold,
        syncStatus: 'pending', // saved locally first, always — sync is best-effort, see below
        gpsLat: coords?.lat ?? null,
        gpsLon: coords?.lon ?? null,
      });
      refreshPendingCount();
      attemptSync(); // fire-and-forget: pushes this (and anything else pending) if online
    } catch (err) {
      Alert.alert('Classification failed', String(err));
    } finally {
      setClassifying(false);
    }
  }

  const belowThreshold = result ? result.confidence < CONFIDENCE_THRESHOLD : false;
  const info = result ? diseaseInfo(cropId, result.predictedClass) : undefined;
  const marketPrice = marketPriceFor(cropId);
  const priceChange = marketPrice ? priceChangePercent(marketPrice) : 0;

  function listenToAction() {
    if (!info) return;
    speakRecommendedAction(info.recommendedAction, 'en');
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>LeafScout</Text>
      <Text style={styles.subtitle}>Offline crop disease diagnosis</Text>

      <Text style={styles.sectionLabel}>Crop</Text>
      <View style={styles.cropRow}>
        {CROPS.filter((c) => AVAILABLE_CROPS.includes(c.id)).map((c) => (
          <TouchableOpacity
            key={c.id}
            style={[styles.cropButton, cropId === c.id && styles.cropButtonActive]}
            onPress={() => {
              setCropId(c.id);
              setResult(null);
              setPhotoUri(null);
            }}>
            <Text style={[styles.cropButtonText, cropId === c.id && styles.cropButtonTextActive]}>
              {c.displayName}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {marketPrice && (
        <View style={styles.priceCard}>
          <View style={styles.priceHeadRow}>
            <Text style={styles.priceLabel}>Market price reference</Text>
            <Text style={styles.priceLabel}>{marketPrice.reference_country}</Text>
          </View>
          <Text style={styles.priceValue}>
            ${marketPrice.latest_avg_usd_per_kg.toFixed(2)} <Text style={styles.priceUnit}>/ kg</Text>
          </Text>
          <Text style={styles.priceSub}>
            {marketPrice.commodity} retail price, {marketPrice.latest_date}.{' '}
            {priceChange >= 0 ? 'Up' : 'Down'} {Math.abs(priceChange).toFixed(0)}% over the last{' '}
            {marketPrice.trend.length} months ({marketPrice.latest_n_markets} markets).
          </Text>
          <Text style={styles.priceNote}>
            An independent price to check against before you sell. Source: {marketPrice.source}.
          </Text>
        </View>
      )}

      <TouchableOpacity
        style={[styles.captureButton, !modelReady && styles.disabledButton]}
        disabled={!modelReady || classifying}
        onPress={pickAndClassify}>
        <Text style={styles.captureButtonText}>
          {modelReady ? 'Pick a leaf photo' : 'Loading model…'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.sampleButton, !modelReady && styles.disabledButton]}
        disabled={!modelReady || classifying}
        onPress={classifySample}>
        <Text style={styles.sampleButtonText}>Try a sample photo instead</Text>
      </TouchableOpacity>

      {photoUri && <Image source={{ uri: photoUri }} style={styles.preview} />}

      {classifying && <ActivityIndicator size="large" style={styles.spinner} />}

      {result && !classifying && (
        <View style={[styles.resultCard, belowThreshold && styles.resultCardWarning]}>
          {belowThreshold ? (
            <>
              <Text style={styles.resultTitleWarning}>Not sure — ask a person</Text>
              <Text style={styles.resultBody}>
                Confidence is too low ({Math.round(result.confidence * 100)}%) to give a
                reliable diagnosis. Show this leaf to your extension officer instead.
              </Text>
            </>
          ) : (
            <>
              <Text style={styles.resultTitle}>{info?.nameEn ?? result.predictedClass}</Text>
              <Text style={styles.confidence}>{Math.round(result.confidence * 100)}% confidence</Text>
              {info && <Text style={styles.resultBody}>{info.descriptionEn}</Text>}
              {info && (
                <View style={styles.actionBox}>
                  <View style={styles.actionHeaderRow}>
                    <Text style={styles.actionLabel}>Recommended action</Text>
                    <TouchableOpacity onPress={listenToAction}>
                      <Text style={styles.listenButtonText}>🔊 Listen</Text>
                    </TouchableOpacity>
                  </View>
                  <Text style={styles.resultBody}>{info.recommendedAction}</Text>
                </View>
              )}
            </>
          )}
          {lastCoords && (
            <Text style={styles.gpsNote}>
              📍 {lastCoords.lat.toFixed(4)}, {lastCoords.lon.toFixed(4)}
            </Text>
          )}
        </View>
      )}

      <Text style={styles.syncNote}>
        {pendingCount} observation{pendingCount === 1 ? '' : 's'} saved offline, pending sync.
        {syncing ? ' Syncing…' : ''}
      </Text>
      {lastSyncNote && <Text style={styles.syncSuccessNote}>{lastSyncNote}</Text>}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f4f6f3' },
  content: { padding: 20, paddingTop: 60, paddingBottom: 60 },
  title: { fontSize: 32, fontWeight: '700', color: '#1f3d2b' },
  subtitle: { fontSize: 15, color: '#55685c', marginBottom: 24 },
  sectionLabel: { fontSize: 13, fontWeight: '600', color: '#55685c', marginBottom: 8 },
  cropRow: { flexDirection: 'row', gap: 8, marginBottom: 20 },
  cropButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#cdd8cf',
    alignItems: 'center',
  },
  cropButtonActive: { backgroundColor: '#1f3d2b', borderColor: '#1f3d2b' },
  cropButtonText: { color: '#1f3d2b', fontWeight: '600', fontSize: 13 },
  cropButtonTextActive: { color: '#fff' },
  captureButton: {
    backgroundColor: '#2f6b3a',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 20,
  },
  disabledButton: { opacity: 0.5 },
  captureButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  priceCard: {
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#d9e3da',
    marginBottom: 20,
  },
  priceHeadRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 2 },
  priceLabel: { fontSize: 11, fontWeight: '700', color: '#55685c', textTransform: 'uppercase' },
  priceValue: { fontSize: 24, fontWeight: '700', color: '#1f3d2b' },
  priceUnit: { fontSize: 14, fontWeight: '500', color: '#55685c' },
  priceSub: { fontSize: 12, color: '#55685c', marginTop: 4, lineHeight: 17 },
  priceNote: { fontSize: 11, color: '#8a968b', marginTop: 6, lineHeight: 15 },
  sampleButton: { alignItems: 'center', paddingVertical: 10, marginBottom: 20 },
  sampleButtonText: { color: '#2f6b3a', fontSize: 14, fontWeight: '600', textDecorationLine: 'underline' },
  preview: { width: '100%', height: 240, borderRadius: 14, marginBottom: 20, backgroundColor: '#ddd' },
  spinner: { marginVertical: 20 },
  resultCard: {
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
    borderColor: '#d9e3da',
    marginBottom: 16,
  },
  resultCardWarning: { backgroundColor: '#fff6e8', borderColor: '#f0cf8a' },
  resultTitle: { fontSize: 20, fontWeight: '700', color: '#1f3d2b' },
  resultTitleWarning: { fontSize: 18, fontWeight: '700', color: '#8a5a00' },
  confidence: { fontSize: 14, color: '#55685c', marginTop: 2, marginBottom: 10 },
  resultBody: { fontSize: 14, color: '#33402f', lineHeight: 20 },
  actionBox: { marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#eef1ea' },
  actionHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  actionLabel: { fontSize: 12, fontWeight: '700', color: '#2f6b3a' },
  listenButtonText: { fontSize: 12, fontWeight: '700', color: '#2f6b3a', textDecorationLine: 'underline' },
  gpsNote: { fontSize: 11, color: '#8a968b', marginTop: 10 },
  syncNote: { fontSize: 12, color: '#8a968b', textAlign: 'center', marginTop: 8 },
  syncSuccessNote: { fontSize: 12, color: '#2f6b3a', textAlign: 'center', marginTop: 4, fontWeight: '600' },
});
