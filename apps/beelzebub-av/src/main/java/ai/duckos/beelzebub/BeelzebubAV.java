package ai.duckos.beelzebub;

import javax.swing.*;
import javax.swing.filechooser.FileNameExtensionFilter;
import java.awt.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

final class BeelzebubAV {
    private static final Color BLACK = new Color(8,8,8), PANEL = new Color(21,21,21),
            RAISED = new Color(36,36,36), YELLOW = new Color(255,212,0),
            WHITE = Color.WHITE, MUTED = new Color(166,166,166), BORDER = new Color(58,58,58);
    private final JFrame frame = new JFrame("Beelzebub AV · DuckOS");
    private final CardLayout pageLayout = new CardLayout();
    private final JPanel pages = new JPanel(pageLayout);
    private final JLabel state = label("READY · Защита по запросу", 12, YELLOW);
    private final JLabel files = label("0", 26, WHITE), detections = label("0", 26, YELLOW), indicators = label("0", 26, WHITE);
    private final JLabel selectedPath = label("Папка не выбрана", 12, MUTED);
    private final JLabel liveState = label("Наблюдение выключено", 13, MUTED);
    private final JLabel progressText = label("Ожидание сканирования", 12, MUTED);
    private final JProgressBar progress = new JProgressBar();
    private final JTextArea log = new JTextArea();
    private final DefaultListModel<ScanResult.Finding> findingModel = new DefaultListModel<>();
    private final JList<ScanResult.Finding> findingList = new JList<>(findingModel);
    private final DefaultListModel<QuarantineService.Entry> quarantineModel = new DefaultListModel<>();
    private final JList<QuarantineService.Entry> quarantineList = new JList<>(quarantineModel);
    private final ExecutorService workers = Executors.newFixedThreadPool(2, task -> {
        Thread thread = new Thread(task, "beelzebub-av-worker"); thread.setDaemon(true); return thread;
    });
    private final AtomicBoolean cancelled = new AtomicBoolean(false);
    private final SignatureCatalog signatures;
    private final ScannerEngine engine;
    private final QuarantineService quarantine;
    private final ScanWatcher watcher;
    private Path directory;
    private boolean scanning;

    static void open() {
        SwingUtilities.invokeLater(() -> {
            try { new BeelzebubAV().show(); }
            catch (Exception error) { JOptionPane.showMessageDialog(null, error.getMessage(), "Beelzebub AV", JOptionPane.ERROR_MESSAGE); }
        });
    }

    private BeelzebubAV() throws Exception {
        signatures = new SignatureCatalog();
        engine = new ScannerEngine(signatures);
        quarantine = new QuarantineService();
        watcher = new ScanWatcher(engine, finding -> SwingUtilities.invokeLater(() -> {
            detections.setText(Integer.toString(Integer.parseInt(detections.getText()) + 1));
            append("LIVE · " + finding.severity() + " · " + finding.path() + " · " + finding.reason());
            state.setText("ALERT · Найден объект для проверки");
        }));
        UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        frame.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE);
        frame.addWindowListener(new java.awt.event.WindowAdapter() {
            @Override public void windowClosing(java.awt.event.WindowEvent event) { close(); }
        });
        frame.setMinimumSize(new Dimension(920,620));
        frame.setSize(1160,740);
        frame.setLocationRelativeTo(null);
        build();
        refreshQuarantine();
        indicators.setText(Integer.toString(signatures.size()));
    }

    private void show() { frame.setVisible(true); }

    private void build() {
        JPanel root = new JPanel(new BorderLayout()); root.setBackground(BLACK);
        JPanel sidebar = new JPanel(); sidebar.setBackground(PANEL); sidebar.setPreferredSize(new Dimension(218,0));
        sidebar.setBorder(BorderFactory.createMatteBorder(0,0,0,1,BORDER));
        sidebar.setLayout(new BoxLayout(sidebar,BoxLayout.Y_AXIS));
        JPanel brand = new JPanel(new BorderLayout(12,0)); brand.setOpaque(false);
        brand.setBorder(BorderFactory.createEmptyBorder(24,18,28,18));
        brand.add(new Mark(),BorderLayout.WEST);
        JPanel brandText = new JPanel(new GridLayout(2,1)); brandText.setOpaque(false);
        brandText.add(label("BEELZEBUB",16,WHITE)); brandText.add(label("DUCKOS SECURITY",9,MUTED));
        brand.add(brandText,BorderLayout.CENTER); sidebar.add(brand);
        nav(sidebar,"OVERVIEW","overview"); nav(sidebar,"SCANNER","scanner");
        nav(sidebar,"LIVE GUARD","guard"); nav(sidebar,"QUARANTINE","quarantine"); nav(sidebar,"SIGNATURES","signatures");
        sidebar.add(Box.createVerticalGlue());
        JPanel footer = new JPanel(new GridLayout(2,1,0,6)); footer.setOpaque(false);
        footer.setBorder(BorderFactory.createEmptyBorder(18,18,22,18));
        footer.add(label("JAVA 17+ · LOCAL ENGINE",9,MUTED)); footer.add(label("MORA BLACK / WHITE / DUCK YELLOW",8,YELLOW)); sidebar.add(footer);

        JPanel header = new JPanel(new BorderLayout()); header.setBackground(BLACK);
        header.setBorder(BorderFactory.createEmptyBorder(20,26,16,26));
        JPanel heading = new JPanel(new GridLayout(2,1,0,5)); heading.setOpaque(false);
        heading.add(label("BEELZEBUB AV",22,WHITE));
        heading.add(label("Endpoint protection · локальное сканирование",12,MUTED));
        header.add(heading,BorderLayout.WEST); header.add(state,BorderLayout.EAST);
        pages.add(overview(),"overview"); pages.add(scanner(),"scanner"); pages.add(guard(),"guard");
        pages.add(quarantinePage(),"quarantine"); pages.add(signaturesPage(),"signatures");
        root.add(sidebar,BorderLayout.WEST); root.add(header,BorderLayout.NORTH); root.add(pages,BorderLayout.CENTER);
        frame.setContentPane(root);
    }

    private void nav(JPanel sidebar,String text,String page) {
        JButton button=button(text,false); button.setHorizontalAlignment(SwingConstants.LEFT);
        button.setMaximumSize(new Dimension(210,46));
        button.addActionListener(event->pageLayout.show(pages,page)); sidebar.add(button);
    }

    private JPanel overview() {
        JPanel panel=content(); panel.setLayout(new BorderLayout(0,20));
        JPanel intro=new JPanel(new BorderLayout(18,0)); intro.setOpaque(false);
        JPanel copy=new JPanel(new GridLayout(3,1,0,8)); copy.setOpaque(false);
        copy.add(label("Ваши файлы. Под вашим контролем.",23,WHITE));
        copy.add(label("Потоковая проверка, локальные индикаторы и обратимый карантин.",13,MUTED));
        copy.add(label("Без скрытых удалений и отправки файлов в облако.",12,YELLOW));
        intro.add(copy,BorderLayout.CENTER); intro.add(new Mark(),BorderLayout.EAST); panel.add(intro,BorderLayout.NORTH);
        JPanel metrics=new JPanel(new GridLayout(2,2,14,14)); metrics.setOpaque(false);
        metrics.add(metric("ФАЙЛЫ ПРОВЕРЕНО",files)); metrics.add(metric("НАХОДКИ",detections));
        metrics.add(metric("ЛОКАЛЬНЫЕ SHA-256 ИНДИКАТОРЫ",indicators));
        JPanel action=card(); action.setLayout(new BorderLayout(0,10));
        action.add(label("БЫСТРОЕ ДЕЙСТВИЕ",10,YELLOW),BorderLayout.NORTH);
        JButton scan=button("Выбрать папку и сканировать",true);
        scan.addActionListener(event->{chooseDirectory(); if(directory!=null){pageLayout.show(pages,"scanner");startScan();}});
        action.add(scan,BorderLayout.CENTER); metrics.add(action); panel.add(metrics,BorderLayout.CENTER);
        JPanel note=card(); note.setLayout(new GridLayout(2,1,0,7));
        note.add(label("СТАТУС ЗАЩИТЫ",10,YELLOW));
        note.add(label("Сканирование по запросу. Live Guard включается отдельно для выбранных папок.",12,MUTED));
        panel.add(note,BorderLayout.SOUTH); return panel;
    }

    private JPanel scanner() {
        JPanel panel=content(); panel.setLayout(new BorderLayout(0,12));
        panel.add(section("СКАНЕР","Рекурсивная проверка без запуска исследуемых файлов"),BorderLayout.NORTH);
        JPanel top=card(); top.setLayout(new BorderLayout(10,9));
        top.add(label("ЦЕЛЕВАЯ ПАПКА",10,YELLOW),BorderLayout.NORTH); top.add(selectedPath,BorderLayout.CENTER);
        JPanel actions=new JPanel(new FlowLayout(FlowLayout.LEFT,8,0)); actions.setOpaque(false);
        JButton choose=button("Выбрать папку",false); choose.addActionListener(e->chooseDirectory()); actions.add(choose);
        JButton start=button("Начать сканирование",true); start.addActionListener(e->startScan()); actions.add(start);
        JButton stop=button("Остановить",false); stop.addActionListener(e->cancelled.set(true)); actions.add(stop);
        JButton isolate=button("Поместить выбранную находку в карантин",false); isolate.addActionListener(e->quarantineFinding()); actions.add(isolate);
        top.add(actions,BorderLayout.SOUTH); panel.add(top,BorderLayout.NORTH);
        JPanel lower=new JPanel(new BorderLayout(0,8)); lower.setOpaque(false);
        progress.setForeground(YELLOW); progress.setBackground(RAISED); lower.add(progress,BorderLayout.NORTH);
        lower.add(progressText,BorderLayout.CENTER);
        findingList.setBackground(PANEL); findingList.setForeground(WHITE);
        findingList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        findingList.setCellRenderer(new DefaultListCellRenderer(){
            @Override public Component getListCellRendererComponent(JList<?> list,Object value,int index,boolean selected,boolean focus){
                JLabel item=(JLabel)super.getListCellRendererComponent(list,value,index,selected,focus);
                if(value instanceof ScanResult.Finding f) item.setText(f.severity()+" · "+f.name()+" · "+f.path());
                item.setBorder(BorderFactory.createEmptyBorder(8,10,8,10));
                item.setBackground(selected?new Color(58,49,0):PANEL); item.setForeground(WHITE); return item;
            }
        });
        lower.add(new JScrollPane(findingList),BorderLayout.CENTER);
        log.setEditable(false); log.setBackground(BLACK); log.setForeground(MUTED); log.setFont(new Font("Monospaced",Font.PLAIN,11));
        log.setRows(5); lower.add(new JScrollPane(log),BorderLayout.SOUTH);
        panel.add(lower,BorderLayout.CENTER); return panel;
    }

    private JPanel guard() {
        JPanel panel=content(); panel.setLayout(new BorderLayout(0,14));
        panel.add(section("LIVE GUARD","Наблюдение за выбранной папкой через Java WatchService"),BorderLayout.NORTH);
        JPanel body=card(); body.setLayout(new GridLayout(5,1,0,12));
        body.add(label("Выберите каталоги, которые нужно отслеживать при создании и изменении файлов.",13,WHITE));
        body.add(liveState);
        JPanel actions=new JPanel(new FlowLayout(FlowLayout.LEFT,8,0)); actions.setOpaque(false);
        JButton choose=button("Выбрать папку",false); choose.addActionListener(e->chooseDirectory()); actions.add(choose);
        JButton start=button("Включить наблюдение",true); start.addActionListener(e->startWatcher()); actions.add(start);
        JButton stop=button("Остановить",false); stop.addActionListener(e->{watcher.close();liveState.setText("Наблюдение выключено");}); actions.add(stop);
        body.add(actions);
        body.add(label("Это не kernel minifilter и не перехватчик всех файловых операций ОС.",11,MUTED));
        body.add(label("Найденные объекты не удаляются автоматически.",11,YELLOW));
        panel.add(body,BorderLayout.NORTH); return panel;
    }

    private JPanel quarantinePage() {
        JPanel panel=content(); panel.setLayout(new BorderLayout(0,12));
        panel.add(section("QUARANTINE","Хеш-проверка, безопасное восстановление, запрет перезаписи"),BorderLayout.NORTH);
        quarantineList.setBackground(PANEL); quarantineList.setForeground(WHITE);
        quarantineList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        quarantineList.setCellRenderer(new DefaultListCellRenderer(){
            @Override public Component getListCellRendererComponent(JList<?> list,Object value,int index,boolean selected,boolean focus){
                JLabel item=(JLabel)super.getListCellRendererComponent(list,value,index,selected,focus);
                if(value instanceof QuarantineService.Entry entry)
                    item.setText(entry.name()+" · "+entry.sha256().substring(0,12)+"… · "+entry.originalPath());
                item.setBorder(BorderFactory.createEmptyBorder(9,12,9,12));
                item.setBackground(selected?new Color(58,49,0):PANEL); item.setForeground(WHITE); return item;
            }
        });
        panel.add(new JScrollPane(quarantineList),BorderLayout.CENTER);
        JPanel actions=new JPanel(new FlowLayout(FlowLayout.LEFT,8,0)); actions.setOpaque(false);
        JButton refresh=button("Обновить список",false); refresh.addActionListener(e->refreshQuarantine()); actions.add(refresh);
        JButton restore=button("Восстановить выбранное",true); restore.addActionListener(e->restoreSelected()); actions.add(restore);
        panel.add(actions,BorderLayout.SOUTH); return panel;
    }

    private JPanel signaturesPage() {
        JPanel panel=content(); panel.setLayout(new BorderLayout(0,14));
        panel.add(section("LOCAL INTELLIGENCE","Пользовательская база SHA-256 · без автообновления из сети"),BorderLayout.NORTH);
        JPanel body=card(); body.setLayout(new GridLayout(5,1,0,12));
        body.add(label("Загружено индикаторов: "+signatures.size(),18,WHITE));
        body.add(label("Формат: SHA256|HIGH|label или SHA256|CRITICAL|label",12,MUTED));
        body.add(label("Импортируйте только базы, которым доверяете. Файл списка локально валидируется.",12,WHITE));
        JButton load=button("Импортировать базу индикаторов",true); load.addActionListener(e->importSignatures()); body.add(load);
        body.add(label("Встроено: EICAR test string и ограниченные эвристики подозрительных команд.",11,YELLOW));
        panel.add(body,BorderLayout.NORTH); return panel;
    }

    private void chooseDirectory() {
        JFileChooser chooser=new JFileChooser(System.getProperty("user.home"));
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
        if(chooser.showOpenDialog(frame)==JFileChooser.APPROVE_OPTION){
            directory=chooser.getSelectedFile().toPath(); selectedPath.setText(directory.toString());
        }
    }

    private void startScan() {
        if(scanning){JOptionPane.showMessageDialog(frame,"Сканирование уже выполняется.");return;}
        if(directory==null){chooseDirectory();if(directory==null)return;}
        scanning=true; cancelled.set(false); progress.setIndeterminate(true);
        progressText.setText("Сканирование запущено…"); state.setText("SCANNING · Анализ файлов");
        findingModel.clear();
        workers.submit(()->{
            try{
                ScanResult result=engine.scan(directory,cancelled,(count,bytes,current)->SwingUtilities.invokeLater(()->{
                    files.setText(Long.toString(count)); progressText.setText(count+" файлов · "+bytes+" байт · "+current.getFileName());
                }));
                SwingUtilities.invokeLater(()->{
                    scanning=false; progress.setIndeterminate(false); detections.setText(Long.toString(result.threatsFound()));
                    state.setText(result.threatsFound()==0?"CLEAN · Совпадений не найдено":"ALERT · Нужна проверка");
                    progressText.setText("Готово · "+result.filesScanned()+" файлов · "+result.threatsFound()+" находок · "+result.duration().toSeconds()+" сек.");
                    result.findings().forEach(f->{findingModel.addElement(f);append(f.severity()+" · "+f.name()+" · "+f.path()+" · "+f.reason());});
                    if(result.cancelled()) append("SCAN · Остановлено пользователем");
                    if(result.failures()>0) append("SCAN · Ошибок чтения: "+result.failures());
                });
            }catch(Exception error){
                SwingUtilities.invokeLater(()->{scanning=false;progress.setIndeterminate(false);state.setText("ERROR · Проверка прервана");append(String.valueOf(error.getMessage()));});
            }
        });
    }

    private void quarantineFinding() {
        ScanResult.Finding finding=findingList.getSelectedValue(); if(finding==null)return;
        int answer=JOptionPane.showConfirmDialog(frame,
                "Переместить найденный файл в карантин?\n"+finding.path()+"\nФайл не будет удалён.",
                "Подтвердить карантин",JOptionPane.YES_NO_OPTION);
        if(answer!=JOptionPane.YES_OPTION)return;
        try{
            QuarantineService.Entry entry=quarantine.quarantine(finding.path());
            refreshQuarantine(); append("QUARANTINED · "+entry.name()+" · "+entry.sha256());
            findingModel.removeElement(finding);
        }catch(Exception error){JOptionPane.showMessageDialog(frame,error.getMessage(),"Карантин не выполнен",JOptionPane.ERROR_MESSAGE);}
    }

    private void startWatcher() {
        if(directory==null){chooseDirectory();if(directory==null)return;}
        try{watcher.start(directory);liveState.setText("Наблюдение включено: "+directory);state.setText("LIVE GUARD · Активно");}
        catch(Exception error){JOptionPane.showMessageDialog(frame,error.getMessage(),"Live Guard",JOptionPane.ERROR_MESSAGE);}
    }

    private void importSignatures() {
        JFileChooser chooser=new JFileChooser();
        chooser.setFileFilter(new FileNameExtensionFilter("SHA-256 indicator list","txt","sha256","db"));
        if(chooser.showOpenDialog(frame)!=JFileChooser.APPROVE_OPTION)return;
        try{
            int count=signatures.importFile(chooser.getSelectedFile().toPath());
            indicators.setText(Integer.toString(signatures.size()));
            JOptionPane.showMessageDialog(frame,"Импортировано индикаторов: "+count,"Beelzebub AV",JOptionPane.INFORMATION_MESSAGE);
        }catch(Exception error){JOptionPane.showMessageDialog(frame,error.getMessage(),"Ошибка базы",JOptionPane.ERROR_MESSAGE);}
    }

    private void refreshQuarantine() {
        try{quarantineModel.clear();for(var entry:quarantine.list())quarantineModel.addElement(entry);}
        catch(Exception error){append("QUARANTINE ERROR · "+error.getMessage());}
    }

    private void restoreSelected() {
        QuarantineService.Entry entry=quarantineList.getSelectedValue();if(entry==null)return;
        int answer=JOptionPane.showConfirmDialog(frame,"Восстановить в исходный путь?\n"+entry.originalPath(),
                "Подтверждение восстановления",JOptionPane.YES_NO_OPTION);
        if(answer!=JOptionPane.YES_OPTION)return;
        try{Path restored=quarantine.restore(entry.id());refreshQuarantine();append("RESTORED · "+restored);}
        catch(Exception error){JOptionPane.showMessageDialog(frame,error.getMessage(),"Восстановление отменено",JOptionPane.ERROR_MESSAGE);}
    }

    private void append(String line){log.append(line+"\n");log.setCaretPosition(log.getDocument().getLength());}
    private void close(){watcher.close();workers.shutdownNow();frame.dispose();}
    private static JPanel content(){JPanel p=new JPanel();p.setBackground(BLACK);p.setBorder(BorderFactory.createEmptyBorder(24,26,24,26));return p;}
    private static JPanel card(){JPanel p=new JPanel();p.setBackground(PANEL);p.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(BORDER),BorderFactory.createEmptyBorder(18,18,18,18)));return p;}
    private static JPanel metric(String title,JLabel value){JPanel p=card();p.setLayout(new GridLayout(2,1,0,8));p.add(label(title,10,YELLOW));p.add(value);return p;}
    private static JPanel section(String title,String subtitle){JPanel p=new JPanel(new GridLayout(2,1,0,6));p.setOpaque(false);p.add(label(title,17,YELLOW));p.add(label(subtitle,12,MUTED));return p;}
    private static JLabel label(String text,int size,Color color){JLabel l=new JLabel(text);l.setFont(new Font("Segoe UI",Font.PLAIN,size));l.setForeground(color);return l;}
    private static JButton button(String text,boolean primary){JButton b=new JButton(text);b.setFont(new Font("Segoe UI",Font.BOLD,12));b.setFocusPainted(false);b.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(primary?YELLOW:BORDER),BorderFactory.createEmptyBorder(10,14,10,14)));b.setBackground(primary?YELLOW:RAISED);b.setForeground(primary?BLACK:WHITE);b.setOpaque(true);return b;}

    private static final class Mark extends JPanel {
        Mark(){setOpaque(false);setPreferredSize(new Dimension(62,62));}
        @Override protected void paintComponent(Graphics graphics){
            Graphics2D g=(Graphics2D)graphics.create();g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);
            g.setColor(YELLOW);g.fillRoundRect(4,4,54,54,16,16);g.setColor(BLACK);g.setFont(new Font("Serif",Font.BOLD,38));g.drawString("B",17,45);
            g.setColor(BLACK);g.drawOval(42,8,8,8);g.dispose();
        }
    }
}
