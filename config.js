window.LIFE_CONFIG={
 id:'local-life-planner',name:'МОЯ НЕДЕЛЯ',subtitle:'Личный план · без аккаунта и облака',title:'Локальный планировщик',
 sections:[
  {id:'life',title:'Личное',type:'routine',visible:true},{id:'work',title:'Работа',type:'routine',visible:true},{id:'home',title:'Дом',type:'routine',visible:true},
  {id:'groceries',title:'Продукты',type:'shopping',visible:true},{id:'household',title:'Для дома',type:'shopping',visible:true},{id:'other',title:'Прочее',type:'shopping',visible:true}
 ],
 tasks:[
  {id:'wake',sectionId:'life',title:'Начать день',time:'07:30',days:[0,1,2,3,4],remind:false,active:true,note:''},
  {id:'breakfast',sectionId:'life',title:'Завтрак',time:'08:00',days:[0,1,2,3,4,5,6],remind:false,active:true,note:''},
  {id:'focus',sectionId:'work',title:'Главная задача дня',time:'09:30',days:[0,1,2,3,4],remind:false,active:true,note:''},
  {id:'lunch',sectionId:'life',title:'Обед',time:'13:00',days:[0,1,2,3,4,5,6],remind:false,active:true,note:''},
  {id:'dinner',sectionId:'life',title:'Ужин',time:'19:00',days:[0,1,2,3,4,5,6],remind:false,active:true,note:''},
  {id:'tomorrow',sectionId:'home',title:'План на завтра',time:'21:30',days:[0,1,2,3,4,5,6],remind:false,active:true,note:''}
 ]
};
